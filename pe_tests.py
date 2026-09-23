import os
import sys

import pe_setup
import pe_session
import pe_global_objects as pe_global


log = pe_global.log


def test_try_fetching_cookies_returns_session_and_keepalive_cookies():
    sys.argv = ["pytest", "authentic.json"]
    pe_setup.setup()
    
    cookies = pe_session.refresh_tokens()
    log.info(cookies)

    assert cookies[pe_session.PHPSESS_NAME] is not None
    assert cookies["keep_alive"] is not None
    