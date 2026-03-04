from requests_oauthlib import OAuth1
import functions_framework
import requests
from requests.auth import HTTPProxyAuth
import logging
from urllib.parse import quote

# ログ設定
logging.basicConfig(level=logging.DEBUG)


@functions_framework.http
def proxy_twitter_request(request):
    try:
        # リクエストデータの取得
        data = request.get_json()
        logging.info(f"Request data received: {data}")

        # 必要なパラメータを取得
        twitter_api_url=data.get('url')
        payload = data.get('payload', {})
        proxy_host = data.get('proxyHost')
        proxy_port = data.get('proxyPort')
        proxy_user = quote(data.get('proxyUser'))
        proxy_password = quote(data.get('proxyPassword'))

        #GAS側のpayloadに含める
        api_key=data.get('api_key')
        api_secret_key=data.get('api_secret_key')
        access_token=data.get('access_token')
        access_token_secret=data.get('access_token_secret')
        oauth = OAuth1(api_key, api_secret_key, access_token, access_token_secret)


        proxy_http = 'http://' + proxy_user + ':' + proxy_password + '@' + proxy_host + ':' + str(proxy_port)
        proxy_https = 'http://' + proxy_user + ':' + proxy_password + '@' + proxy_host + ':' + str(proxy_port)

        proxies = {'http' : proxy_http, 'https': proxy_https}
        logging.info(f"Proxies: {proxies}")


        # メディアアップロードの場合
        if "upload.twitter.com" in twitter_api_url:
            logging.info("Uploading media...")

            headers = {"Content-Type": "application/x-www-form-urlencoded"}  # 追加
            response = requests.post(
                twitter_api_url,
                data=payload,  # 変更: JSON ではなく URL エンコード形式
                headers=headers,  # 追加
                proxies=proxies,
                verify=False,
                auth=oauth,
                timeout=10
            )
        # user情報取得（get）
        elif "users/me" in twitter_api_url or "fields=non_public_metrics" in twitter_api_url:
            response = requests.get(
                twitter_api_url,
                json=payload,
                proxies=proxies,
                verify=False,
                auth=oauth,
                timeout=10
            )
        else:
            response = requests.post(
                twitter_api_url,
                json=payload,
                proxies=proxies,
                verify=False,
                auth=oauth,
                timeout=10
            )

        # 実際に送信するリクエストデータをログに出力
        logging.info(f"Request URL: {twitter_api_url}")
        logging.info(f"Payload: {payload}")

        # レスポンスのログ出力
        logging.info(f"Response status: {response.status_code}")
        logging.info(f"Response body: {response.text}")

        # 成功時のレスポンス
        return (response.json(), response.status_code)
    
    except requests.exceptions.ProxyError as proxy_error:
        logging.error(f"ProxyError: {str(proxy_error)}")
        return ({"error": "Proxy connection failed", "details": str(proxy_error)}, 500)

    except requests.exceptions.RequestException as request_error:
        logging.error(f"RequestException: {str(request_error)}")
        return ({"error": "Request failed", "details": str(request_error)}, 500)

    except Exception as e:
        logging.error(f"Unexpected Error: {str(e)}")
        return ({"error": "Unexpected error occurred", "details": str(e)}, 500)
