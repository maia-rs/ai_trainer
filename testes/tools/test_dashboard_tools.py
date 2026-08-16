from app.tools.dashboard import gerar_link_dashboard as dashboard_module


def test_gerar_link_dashboard_sucesso():
    resultado = dashboard_module.gerar_link_dashboard.invoke(
        {"usuario_id": "user-1", "expira_em_minutos": 30}
    )

    assert resultado["url"].startswith("https://aitrainer.local/dashboard/user-1?token=")
    assert resultado["expires_in_minutes"] == 30
    assert "expires_at" in resultado


def test_gerar_link_dashboard_minimo_um_minuto():
    resultado = dashboard_module.gerar_link_dashboard.invoke(
        {"usuario_id": "user-1", "expira_em_minutos": 0}
    )

    assert resultado["expires_in_minutes"] == 1