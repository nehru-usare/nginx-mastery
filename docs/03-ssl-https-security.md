# Level 3: SSL, HTTPS & Security

## 1. SSL/TLS Explained
SSL (Secure Sockets Layer) and its direct successor TLS (Transport Layer Security) are cryptographic protocols designed to provide communications security over a computer network.
They provide:
- **Encryption**: Hides data in transit from eavesdroppers.
- **Authentication**: Verifies that the server you are talking to is who it claims to be.
- **Integrity**: Ensures the data wasn't modified in transit.

HTTPS is simply HTTP running over TLS. NGINX excels at "SSL Termination", acting as the barrier that decrypts traffic before forwarding it unencrypted to backend servers via an isolated private network.

## 2. Setting Up a Self-Signed Certificate
Self-signed certificates are not verified by a trusted Certificate Authority (CA) and will show warnings in root browsers, but they are great for local testing.

Generate the certificate:
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/nginx-selfsigned.key \
  -out /etc/nginx/ssl/nginx-selfsigned.crt
```

Configure NGINX:
```nginx
server {
    listen 443 ssl;
    server_name local.example.com;

    ssl_certificate /etc/nginx/ssl/nginx-selfsigned.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx-selfsigned.key;

    location / {
        root /usr/share/nginx/html;
        index index.html;
    }
}
```

## 3. Let's Encrypt Overview
Let’s Encrypt is a free, automated, and open certificate authority. By using `certbot` alongside NGINX, you can auto-provision valid SSL certificates for your domain.

Typically run via:
```bash
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo certbot --nginx -d example.com -d www.example.com
```
Certbot automatically amends your `nginx.conf` and injects the `ssl_certificate` pathways.

## 4. HTTP to HTTPS Redirect
To enforce security, redirect all port 80 traffic to port 443.

```nginx
server {
    listen 80;
    server_name example.com www.example.com;
    
    # 301 Permanent Redirect
    return 301 https://$host$request_uri;
}
```

## 5. Security Headers
Add these headers inside your `server` block to mitigate common web attacks (like XSS, Clickjacking).

```nginx
server {
    listen 443 ssl;
    # ... ssl config ...

    # Prevents Clickjacking
    add_header X-Frame-Options "SAMEORIGIN" always;
    
    # Prevents MIME-sniffing
    add_header X-Content-Type-Options "nosniff" always;
    
    # Enables XSS filtering
    add_header X-XSS-Protection "1; mode=block" always;
    
    # HTTP Strict Transport Security (HSTS) - Forces HTTPS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Controls HTTP Referer header
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
```

## 6. Rate Limiting
Protect your application from brute-force or DDoS attacks using `limit_req`.

Step 1: Define a zone in the `http` block.
```nginx
http {
    # limit by binary remote address, allocate 10MB memory, rate is 1 request per second
    limit_req_zone $binary_remote_addr zone=mylimit:10m rate=1r/s;
}
```

Step 2: Apply the zone in a `location` block.
```nginx
server {
    location /login {
        limit_req zone=mylimit burst=5 nodelay;
        proxy_pass http://backend;
    }
}
```
*Burst* allows short spikes up to 5 requests without getting immediately rejected.

## 7. Basic Authentication
Password-protect specific paths using `htpasswd`.

Generate a password file:
```bash
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin_user
```

Configure NGINX:
```nginx
location /admin {
    auth_basic "Restricted Administrator Area";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://backend;
}
```

## 8. IP Restriction
Allow or deny access based on IP addresses. NGINX processes these top-down.

```nginx
location /internal-api {
    allow 192.168.1.0/24; # Allow local network
    allow 10.0.0.5;       # Allow specific IP
    deny all;             # Deny everyone else
    
    proxy_pass http://backend;
}
```

## 9. CORS Configuration
Cross-Origin Resource Sharing (CORS) manages which external domains can access your APIs via browsers.

```nginx
location /api/ {
    if ($request_method = 'OPTIONS') {
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
        add_header 'Access-Control-Max-Age' 1728000;
        add_header 'Content-Type' 'text/plain; charset=utf-8';
        add_header 'Content-Length' 0;
        return 204;
    }

    add_header 'Access-Control-Allow-Origin' '*' always;
    proxy_pass http://backend;
}
```

## 10. Secure Production-Ready Example
Putting it all together.

```nginx
http {
    limit_req_zone $binary_remote_addr zone=mylimit:10m rate=10r/s;

    server {
        listen 80;
        server_name api.example.com;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.example.com;

        ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        
        add_header Strict-Transport-Security "max-age=31536000" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;

        location / {
            limit_req zone=mylimit burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /metrics {
            allow 10.0.0.0/8;
            deny all;
            proxy_pass http://backend/metrics;
        }
    }
}
```

## 11. Interview Preparation (Level 3)

1. **How would you debug a 502 Bad Gateway error when SSL is placed onto NGINX?**
   *Answer:* A 502 indicates NGINX cannot communicate with the upstream backend. Often this is because NGINX is making a proxy_pass using `https://` when the backend is only listening on `http://`, or vice versa. Checking `error.log` is the mandatory first step.

2. **What does the `nodelay` flag do in a `limit_req` directive?**
   *Answer:* Without `nodelay`, NGINX artificially delays requests that exceed the rate limit (but are within the burst limit) so they conform to the exact defined rate. With `nodelay`, NGINX processes burst requests immediately, only returning 503 errors when the burst queue fills up.

3. **What is SSL Termination and why is it beneficial?**
   *Answer:* SSL Termination is the practice of decrypting SSL/TLS traffic at the load balancer or proxy level. It's beneficial because it offloads the CPU-intensive cryptography operations from the backend servers, and simplifies certificate management since you only install certificates on the proxy.

4. **Why is the HSTS (`Strict-Transport-Security`) header important?**
   *Answer:* It tells browsers to strictly communicate over HTTPS, even if the user manually types `http://`. This protects against downgrade attacks and cookie-hijacking.
