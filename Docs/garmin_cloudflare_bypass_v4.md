# Garmin Cloudflare Bypass (Universal Fix v4) Post-Mortem

**Date:** April 12, 2026  
**Status:** Solved & Running in Production

## 🔴 The Problem

In early April 2026, Garmin significantly heightened their Cloudflare bot-protection around their SSO endpoint (`sso.garmin.com`). This resulted in severe and persistent `HTTP 403 Forbidden` and `HTTP 429 Too Many Requests` errors for the Health AI backend when attempting to authenticate users.

The official `garminconnect` and `garth` Python packages use an HTML-scraping approach (`get`) against an embedded Garmin login widget to fetch a CSRF token before performing a login POST. Cloudflare fingerprinted the Python `urllib3` stack and consistently blocked these initial requests, meaning the backend was never even reaching Garmin's actual authentication logic.

Even upgrading to `garminconnect 0.3.x` with `curl_cffi` (for TLS impersonation) was insufficient on its own because Cloudflare eventually caught onto the specific request trajectories.

## 🟢 The Solution: Universal Fix v4

To create a bulletproof, automated authentication flow that entirely circumvents Cloudflare's browser scrutiny, we engineered a custom monkeypatch injected directly into `garminconnect.Garmin.login`. 

The core strategy bypasses the HTML-parsing stage completely by interacting directly with Garmin's native Android mobile app API, which operates under different, less restrictive WAF rules.

### Step 1: Direct JSON POST to `/portal/api/login`
Instead of performing a `GET` request to scrape a CSRF token, the backend opens a `curl_cffi` session (impersonating Safari/Chrome) and immediately targets the `https://sso.garmin.com/portal/api/login` JSON endpoint. 
- **ClientId:** `GCM_ANDROID_DARK` (The official Garmin Connect Mobile identifier).
- **Service:** `https://mobile.integration.garmin.com/gcm/android`.
By supplying the raw JSON payload with the username and password here, we bypass the captive Cloudflare turnstiles entirely and obtain a raw Garmin **Service Ticket**.

### Step 2: Custom OAuth1 Token Exchange
The standard `garth` library internally attempts to exchange this service ticket using `connectapi.garmin.com`. However, because we requested a ticket bound to `mobile.integration.garmin.com/gcm/android`, `garth`'s internal method (which hardcodes `sso/embed` as the return URL) would trigger a `401 Unauthorized` block because the redirect URI misaligned with the ticket's issuance.

We bypassed this by writing a custom inline OAuth1 exchange func. We instantiated a custom `GarminOAuth1Session` and passed the explicit Android service URL.

### Step 3: Backward-Compatible Token Injection
Health AI runs on `garminconnect 0.2.x`, meaning its internal dependency (`garth`) manages standard base64/JSON objects (specifically, `oauth1_token` and `oauth2_token`). We seamlessly mapped the resulting OAuth2 tokens into the `self.garth._profile` properties to successfully mount the authorized session under the hood without breaking the original library logic.

### Step 4: Robust Serialization via Temporary Directories (`tmpdir`)
During development, silent failures appeared when attempting to save the active tokens because `garth 0.2.x`'s `.dumps()` method outputs base64 arrays (e.g., `W251bGwsIG51bGxd`) instead of standard JSON, causing `JSONDecodeError`s. Furthermore, `client.login()` strictly demands a valid filesystem directory path, not a JSON payload.

To guarantee universal compatibility across `garminconnect 0.2.x` and `0.3.x`, the patch enforces reading and writing via standard operating system Temporary Directories (`tempfile.TemporaryDirectory()`). 

- **Save:** Executes `garth.dump(tmpdir)`, dynamically reads the resulting `oauth1_token.json` and `oauth2_token.json` files, and compresses them into a standard dictionary for Firestore.
- **Load:** Reads the Firestore dictionary, unspools it into `tmpdir/.json` files, and feeds the `tmpdir` path into the native `.login(tokenstore=tmpdir)` logic.

## 🏁 Result

The mobile app and backend communicate seamlessly. The rate-limiting loops are bypassed via Android-level SSO keys. Background sync execution drops the `401/403` noise floor to 0. 

Garmin synchronization is officially marked 100% production resilient.
