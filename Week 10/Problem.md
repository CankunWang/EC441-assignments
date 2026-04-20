# Week 10 - Web, HTTP, and HTML Problem

## Topic

Application layer: Web, HTTP, HTML

## Type

Problem with worked solution

---

## Problem

A student uses a browser to visit a simple banking website at:

`http://bank.example.com/login.html`

Assume the site uses HTTP/1.1.

### 1. Initial page fetch

1. What HTTP method is normally used to fetch `login.html`?
2. What resource path appears in the request line?
3. Why is the `Host` header needed in HTTP/1.1?
4. Which part of the request tells the server which page is being requested?

Write one reasonable request example including:

- request line
- `Host`
- `User-Agent`
- `Connection`

### 2. Server response for the login page

Server response:

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 5120
Set-Cookie: sid=abc123; HttpOnly
```

1. What does status code `200` mean?
2. What does `Content-Type: text/html` tell the browser?
3. What is the purpose of `Content-Length`?
4. What does the cookie likely represent?
5. What does `HttpOnly` try to protect against?

### 3. Form submission

The login page contains an HTML form:

```html
<form action=/session method=post>
  <input name=username>
  <input name=password type=password>
</form>
```

The user enters:

- username = `alice`
- password = `net123`

1. What HTTP method is used when the form is submitted?
2. What path is requested?
3. Give one reasonable message body for this submission.
4. Why is `POST` a better choice than `GET` here?
5. What header usually describes the format of the submitted body?

### 4. Redirect after login

Server response after login:

```http
HTTP/1.1 302 Found
Location: /accounts
Set-Cookie: sid=xyz789; HttpOnly
```

1. What does status code `302` mean?
2. What does the browser do next?
3. What is the purpose of the `Location` header?
4. In the next request, how is the cookie used?
5. Why is a cookie useful for a login-based site?

### 5. Fetching embedded objects

The `/accounts` page is HTML and contains:

```html
<img src=/logo.png>
<script src=/app.js></script>
```

1. Does the browser automatically fetch these extra objects?
2. Are `logo.png` and `app.js` usually part of the same HTTP response as the HTML, or separate HTTP requests?
3. Why can one HTML page lead to multiple HTTP transactions?
4. Which course topic does this illustrate: physical layer, routing, or application layer?

### 6. Short status-code reasoning

For each status code below, briefly state what it means:

1. `200 OK`
2. `301 Moved Permanently`
3. `302 Found`
4. `404 Not Found`

---

## Solution

### 1. Initial page fetch

1. The method is `GET`.
2. The path is `/login.html`.
3. `Host` identifies the target site on a shared IP.
4. The request line, especially `GET /login.html HTTP/1.1`, identifies the page.

Example:

```http
GET /login.html HTTP/1.1
Host: bank.example.com
User-Agent: Mozilla/5.0
Connection: close
```

### 2. Server response for the login page

1. `200 OK` means the request succeeded.
2. `Content-Type: text/html` means the body is HTML.
3. `Content-Length` gives the body size in bytes.
4. The cookie is likely a session ID.
5. `HttpOnly` helps prevent client-side scripts from reading the cookie.

### 3. Form submission

1. The method is `POST`.
2. The requested path is `/session`.
3. Example body:

```text
username=alice&password=net123
```

4. `POST` is better because credentials should not appear in the URL.
5. The header is usually:

```http
Content-Type: application/x-www-form-urlencoded
```

### 4. Redirect after login

1. `302 Found` tells the browser to request another URL.
2. The browser usually requests `/accounts` next.
3. The `Location` header tells the browser where to go next.
4. In the next request, the browser includes the cookie, for example:

```http
Cookie: sid=xyz789
```

5. A cookie lets the server link later requests to the same logged-in user.

### 5. Fetching embedded objects

1. Yes. After parsing the HTML, the browser automatically requests referenced objects such as images and scripts.
2. They are usually fetched with separate HTTP requests.
3. One HTML page can reference many resources, so one page load can trigger many HTTP requests.
4. This illustrates the application layer.

### 6. Short status-code reasoning

1. `200 OK`: the request succeeded.
2. `301 Moved Permanently`: the resource has a new permanent URL.
3. `302 Found`: the resource is temporarily available at another URL.
4. `404 Not Found`: the resource was not found.
