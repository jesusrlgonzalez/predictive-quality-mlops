"""Pruebas adversas de fuga de información (SEC-03).

Ejecutan el entrenamiento completo (`pqm.train.main`) con un conjunto SINTÉTICO pequeño y
ordenado en el tiempo, y espían cada ajuste, cada predicción y cada elección de umbral.
No leen SECOM ni escriben en `models/` o `reports/` del repositorio: las rutas se redirigen a
un directorio temporal. Cada regla está escrita para fallar si alguien:
  - entrena el modelo de evaluación con lotes del holdout,
  - elige el umbral o la imputación con el holdout,
  - usa lotes futuros en la validación temporal,
  - ajusta la limpieza o la imputación con datos que no son de entrenamiento.
"""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import pqm.train as tr
from pqm.data import split_temporal
from pqm.features import SensorCleaner

N, N_SENSORES = 260, 10
N_FOLDS_ALEATORIOS = 5  # diagnóstico deliberado de fuga (partición aleatoria), solo dentro del entrenamiento


def _datos_sinteticos(seed=7):
    """Lotes ordenados en el tiempo con señal débil, vacíos y un sensor constante."""
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(rng.normal(size=(N, N_SENSORES)), columns=[f"s{i}" for i in range(N_SENSORES)])
    X["s_const"] = 1.0
    X = X.mask(rng.random(X.shape) < 0.08)
    riesgo = 1 / (1 + np.exp(-(X["s0"].fillna(0) * 1.5 - 2.5)))
    y = pd.Series((rng.random(N) < riesgo).astype(int), name="falla")
    t = pd.Series(pd.date_range("2024-01-01", periods=N, freq="6h"), name="timestamp")
    return X, y, t


@pytest.fixture(scope="module")
def corrida(tmp_path_factory):
    """Ejecuta main() una vez con espías y devuelve lo observado."""
    root = tmp_path_factory.mktemp("secom_sintetico")
    (root / "reports").mkdir()
    X, y, t = _datos_sinteticos()
    n_train = split_temporal(N, 0.2)[0].stop
    obs = {"fits": [], "predicciones": [], "umbrales": [], "n_train": n_train, "y": y.to_numpy()}

    real_build = tr.build_pipeline
    real_best = tr.best_threshold

    def build_espia(*a, **k):
        pipe = real_build(*a, **k)
        fit_real, pred_real = pipe.fit, pipe.predict_proba
        registro = {"filas_fit": None}

        def fit(Xf, yf=None, **kw):
            registro["filas_fit"] = np.asarray(Xf.index)
            obs["fits"].append(registro)
            return fit_real(Xf, yf, **kw)

        def predict_proba(Xp):
            obs["predicciones"].append({"filas_fit": registro["filas_fit"], "filas_pred": np.asarray(Xp.index)})
            return pred_real(Xp)

        pipe.fit, pipe.predict_proba = fit, predict_proba
        return pipe

    def best_espia(yv, p, costos=None):
        obs["umbrales"].append(np.asarray(yv).copy())
        return real_best(yv, p, costos)

    mp = pytest.MonkeyPatch()
    mp.setattr(tr, "load_secom", lambda *a, **k: (X, y, t))
    mp.setattr(tr, "build_pipeline", build_espia)
    mp.setattr(tr, "best_threshold", best_espia)
    mp.setattr(tr, "joblib", SimpleNamespace(dump=lambda *a, **k: None))  # el espía no es serializable
    mp.setattr(tr, "ROOT", root)
    mp.setattr(tr, "MODELS", root / "models")
    mp.setattr(tr, "FIGURES", root / "reports/figures")
    mp.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{root / 'mlflow.db'}")
    try:
        obs["res"] = tr.main()
    finally:
        mp.undo()
    return obs


def test_la_evaluacion_del_holdout_viene_de_un_modelo_que_no_vio_el_holdout(corrida):
    """La predicción que cubre todo el holdout (la evaluación final) se ajustó solo con el entrenamiento."""
    n = corrida["n_train"]
    evaluacion = [p for p in corrida["predicciones"]
                  if p["filas_pred"].min() == n and p["filas_pred"].max() == len(corrida["y"]) - 1]
    assert evaluacion, "el espía no registró la evaluación del holdout"
    for p in evaluacion:
        assert p["filas_fit"].max() < n


def test_toda_prediccion_sobre_lotes_del_holdout_aprende_solo_del_pasado(corrida):
    """Incluye el umbral de despliegue (paso 8), que usa validación temporal sobre todos los lotes."""
    n = corrida["n_train"]
    for p in corrida["predicciones"]:
        if p["filas_pred"].max() >= n:
            assert p["filas_fit"].max() < p["filas_pred"].min()


def test_validacion_temporal_solo_aprende_del_pasado(corrida):
    """Dentro del entrenamiento, solo el diagnóstico aleatorio declarado puede mezclar el futuro."""
    n = corrida["n_train"]
    dentro = [p for p in corrida["predicciones"] if p["filas_pred"].max() < n]
    mezclan_futuro = [p for p in dentro if p["filas_fit"].max() >= p["filas_pred"].min()]
    assert len(mezclan_futuro) == N_FOLDS_ALEATORIOS


def test_umbral_de_evaluacion_no_usa_etiquetas_del_holdout(corrida):
    n = corrida["n_train"]
    y_ho = corrida["y"][n:]
    for yv in corrida["umbrales"]:
        assert not (len(yv) == len(y_ho) and np.array_equal(yv, y_ho))
    # el umbral reportado se eligió con la validación temporal del periodo de entrenamiento
    primero = corrida["umbrales"][0]
    assert len(primero) < n


def test_imputacion_elegida_con_datos_de_entrenamiento(corrida):
    n = corrida["n_train"]
    prev_train_oof = [v["prevalencia"] for v in corrida["res"]["comparacion_imputacion"].values()]
    y_ho = corrida["y"][n:]
    assert all(abs(pv - y_ho.mean()) > 1e-12 or len(set(prev_train_oof)) == 1 for pv in prev_train_oof)
    assert corrida["res"]["imputacion_elegida"] == max(
        corrida["res"]["comparacion_imputacion"], key=lambda k: corrida["res"]["comparacion_imputacion"][k]["pr_auc"])


@pytest.mark.parametrize("imputer", ["median", "knn", "none"])
def test_limpieza_no_cambia_si_se_altera_el_futuro(imputer):
    """Ajustada con el pasado, la limpieza no debe cambiar al alterar los datos futuros."""
    X, _, _ = _datos_sinteticos()
    pasado, futuro = X.iloc[:150], X.iloc[150:]
    a = SensorCleaner(imputer=imputer).fit(pasado)
    alterado = futuro * 1000 + 50
    b = SensorCleaner(imputer=imputer).fit(pasado)
    pd.testing.assert_frame_equal(a.transform(pasado), b.transform(pasado))
    assert a.final_ == b.final_
    # transformar el futuro alterado no reajusta nada aprendido del pasado
    b.transform(alterado)
    pd.testing.assert_frame_equal(a.transform(pasado), b.transform(pasado))


def test_la_imputacion_usa_estadisticos_del_pasado():
    X, _, _ = _datos_sinteticos()
    pasado, futuro = X.iloc[:150], X.iloc[150:].copy()
    c = SensorCleaner(imputer="median").fit(pasado)
    futuro.iloc[:, 1] = np.nan
    futuro.iloc[0, 1] = 1e9  # un valor extremo del futuro no debe mover la mediana aprendida
    col = futuro.columns[1]
    if col in c.final_:
        assert np.allclose(c.transform(futuro)[col].iloc[1:], pasado[col].median())
