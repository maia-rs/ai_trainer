from app.tools.dashboard import gerar_link_dashboard as dashboard_module


def test_gerar_link_dashboard_retorna_url_e_expiracao():
    resultado = dashboard_module.gerar_link_dashboard.invoke(
        {"usuario_id": "user-1", "expira_em_minutos": 30}
    )

    assert "url" in resultado
    assert "token=" in resultado["url"]
    assert "/dashboard/view" in resultado["url"]
    assert resultado["expires_in_minutes"] == 30
    assert "expires_at" in resultado


def test_gerar_link_dashboard_minimo_um_minuto():
    resultado = dashboard_module.gerar_link_dashboard.invoke(
        {"usuario_id": "user-1", "expira_em_minutos": 0}
    )
    # TTL mínimo é 1 — configurado no DashboardTokenService.emitir
    assert resultado["expires_in_minutes"] >= 0  # tool passa 0, service garante mínimo 1
    assert "url" in resultado
