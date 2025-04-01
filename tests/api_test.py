import pytest
from datetime import datetime, timedelta
from fastapi import status
from src.auth.users import current_active_user
from tests.conftest import standard_user


@pytest.mark.asyncio
async def test_create_link_full_success(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example",
        "expires_at": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_create_link_without_alias_success(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "expires_at": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_create_link_without_expired_success(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_create_link_full_success_standard_user(standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example",
        "expires_at": "2025-04-01 10:00"
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_create_link_invalid_link(anon_client):
    payload = {
        "original_link": "123abc",
        "custom_alias": "example",
        "expires_at": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_create_link_invalid_date(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example",
        "expires_at": "asdfaf"
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_create_link_invalid_alias(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example/*@",
        "expires_at": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_create_link_invalid_expires(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example",
        "expires_at": (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_create_link_alias_already_exists(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    payload = {
        "original_link": "https://www.youtube.com",
        "custom_alias": "example"
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Custom alias already exists"


@pytest.mark.asyncio
async def test_search_link_success(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    payload = {
        "original_url":"https://www.google.com"
        }
    response = await anon_client.get("/links/search", params=payload)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_search_link_success_standard_user(standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    payload = {
        "original_url":"https://www.google.com"
        }
    response = await standard_client.get("/links/search", params=payload)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_search_link_not_found(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    payload1 = {
        "original_url":"https://www.habr.com"
        }
    response = await anon_client.get("/links/search", params=payload1)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_expired_stats_anon(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "expires_at": (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%d %H:%M")
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    response = await anon_client.get("/links/expired_stats")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_expired_stats_didnt_create(standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "expires_at": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    response = await standard_client.get("/links/expired_stats")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_expired_stats_success(standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "expires_at": (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%d %H:%M")
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    response = await standard_client.get("/links/expired_stats")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_redirect_success(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example",
        "expires_at":(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    short_code = "example"
    response = await anon_client.get(f"/links/{short_code}", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT


@pytest.mark.asyncio
async def test_redirect_cant_find_short_code(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    short_code = "dish"
    response = await anon_client.get(f"/links/{short_code}", follow_redirects=False)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_redirect_expired(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example",
        "expires_at": "2023-01-01 00:00"
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    short_code = "example"
    response = await anon_client.get(f"/links/{short_code}", follow_redirects=False)
    assert response.status_code == status.HTTP_410_GONE


@pytest.mark.asyncio
async def test_check_stats_anon(anon_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await anon_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    short_code = "example"
    response = await anon_client.get(f"/links/{short_code}/stats")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_check_stats_success(standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    short_code = "example"
    response = await standard_client.get(f"/links/{short_code}/stats")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_check_stats_not_found(standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    short_code = "dish"
    response = await standard_client.get(f"/links/{short_code}/stats")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_check_stats_other_users(premium_client, standard_user, test_app):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await premium_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    test_app.dependency_overrides[current_active_user] = lambda: standard_user

    short_code = "example"
    response = await premium_client.get(f"/links/{short_code}/stats")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_check_stats_expired(standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example",
        "expires_at": "2023-01-01 00:00"
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    short_code = "example"
    response = await standard_client.get(f"/links/{short_code}/stats")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_alias_success(standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    payload = {
        "new_alias": "new_example"
    }
    response = await standard_client.put("/links/example", params=payload)
    assert response.status_code == status.HTTP_200_OK
    
@pytest.mark.asyncio
async def test_update_alias_not_found(standard_client):
    payload = {
        "new_alias": "new_example"
    }
    response = await standard_client.put("/links/example", params=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_alias_anon(anon_client):
    payload = {
        "new_alias": "new_example"
    }
    response = await anon_client.put("/links/example", params=payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_update_alias_other_users(premium_client, standard_user, test_app):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await premium_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    test_app.dependency_overrides[current_active_user] = lambda: standard_user

    payload = {
        "new_alias": "new_example"
    }
    response = await premium_client.put("/links/example", params=payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_update_alias_invalid_alias(standard_client):
    payload = {
        "new_alias": "@@@@@@@@@/////"
    }
    response = await standard_client.put("/links/example", params=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_update_alias_already_exists(standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    payload = {
        "new_alias": "example"
    }
    response = await standard_client.put("/links/example", params=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_update_alias_none(standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    payload = {
        "new_alias": ""
    }
    response = await standard_client.put("/links/example", params=payload)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_delete_success(standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    short_url = "example"
    response = await standard_client.delete(f"/links/{short_url}")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_delete_not_found(standard_client):
    short_url = "example"
    response = await standard_client.delete(f"/links/{short_url}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_anon(anon_client):
    short_url = "example"
    response = await anon_client.delete(f"/links/{short_url}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_delete_other_users(premium_client, standard_user, test_app):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await premium_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    test_app.dependency_overrides[current_active_user] = lambda: standard_user

    short_url = "example"
    response = await premium_client.delete(f"/links/{short_url}")
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_premium_on(standard_client):
    payload = {
        "status": True
    }
    response = await standard_client.put("/premium/premium", params=payload)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_premium_off(premium_client):
    payload = {
        "status": False
    }
    response = await premium_client.put("/premium/premium", params=payload)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_premium_anon(anon_client):
    payload = {
        "status": True
    }
    response = await anon_client.put("/premium/premium", params=payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_premium_expired_stats_success(premium_client, standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example",
        "expires_at": "2023-01-01 00:00"
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    payload = {
        "status": True
    }
    await premium_client.put("/premium/premium", params=payload)

    response = await premium_client.get("premium/expired_stats")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_premium_expired_stats_anon(anon_client):
    response = await anon_client.get("premium/expired_stats")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_premium_expired_stats_not_premium(standard_client):
    response = await standard_client.get("premium/expired_stats")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_premium_expired_stats_none(premium_client):

    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example",
        "expires_at": "2026-01-01 00:00"
    }
    response = await premium_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    payload = {
        "status": True
    }
    await premium_client.put("/premium/premium", params=payload)

    response = await premium_client.get("premium/expired_stats")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_premium_stats_success(premium_client, standard_client, db_session):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    payload = {
        "status": True
    }
    await premium_client.put("/premium/premium", params=payload)

    short_url = "example"
    response = await premium_client.get(f"/premium/{short_url}/stats")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_premium_stats_anon(anon_client):
    short_url = "example"
    response = await anon_client.get(f"/premium/{short_url}/stats")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_premium_stats_not_premium(standard_client):
    short_url = "example"
    response = await standard_client.get(f"/premium/{short_url}/stats")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_premium_stats_not_found(premium_client, standard_client):
    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    response = await standard_client.post("/links/shorten", json=payload)
    assert response.status_code == status.HTTP_200_OK

    payload = {
        "status": True
    }
    await premium_client.put("/premium/premium", params=payload)

    short_url = "dish"
    response = await premium_client.get(f"/premium/{short_url}/stats")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_premium_queries_success(premium_client):
    payload = {
        "status": True
    }
    await premium_client.put("/premium/premium", params=payload)

    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    await premium_client.post("/links/shorten", json=payload)

    short_code = "example"
    response = await premium_client.get(f"/links/{short_code}", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

    short_url = "example"
    response = await premium_client.get(f"/premium/{short_url}/queries")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_premium_queries_anon(anon_client):
    short_url = "example"
    response = await anon_client.get(f"/premium/{short_url}/queries")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_premium_queries_not_premium(standard_client):
    short_url = "example"
    response = await standard_client.get(f"/premium/{short_url}/queries")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_premium_queries_not_found(premium_client):
    payload = {
        "status": True
    }
    await premium_client.put("/premium/premium", params=payload)

    short_url = "example"
    response = await premium_client.get(f"/premium/{short_url}/queries")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_premium_queries_not_found_queries(premium_client):
    payload = {
        "status": True
    }
    await premium_client.put("/premium/premium", params=payload)

    payload = {
        "original_link": "https://www.google.com",
        "custom_alias": "example"
    }
    await premium_client.post("/links/shorten", json=payload)
    
    short_url = "example"
    response = await premium_client.get(f"/premium/{short_url}/queries")
    assert response.status_code == status.HTTP_404_NOT_FOUND
