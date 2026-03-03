# Level 7: Production Deployment

## 1. Zero Downtime Reloads
In production, you never "restart" NGINX to apply a new configuration. Restarting drops active connections. Instead, you "reload" NGINX.

```bash
nginx -s reload
```
**How it works (Graceful Restart):**
1. The **Master** process verifies the new `nginx.conf` syntax.
2. If valid, it spawns **new** worker processes using the new configuration.
3. It sends a message to the **old** worker processes asking them to shut down gracefully.
4. Old workers stop accepting new connections but wait for current active connections to finish (e.g., large file downloads) before dying.

*In Docker:*
```bash
docker exec nginx_container nginx -s reload
```

## 2. Container Best Practices
When deploying NGINX inside Docker, follow these rules:

- **Use Lightweight Base Images**: e.g., `nginx:mainline-alpine` (Smaller attack surface).
- **Run as Non-Root**: NGINX master process runs as root to bind port 80/443. The worker processes run as the `nginx` user. Ensure your mounted files have read permissions for the `nginx` user. 
- **Read-Only Configurations**: Always mount your `nginx.conf` and certificates as read-only (`:ro`).
    ```yaml
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    ```
- **Forward Logs to stdout/stderr**: Docker natively captures these. Official NGINX images already symlink `/var/log/nginx/access.log` to `/dev/stdout`.

## 3. Deployment Strategies

### Blue-Green Deployment
You maintain two identical environments: Blue (active production) and Green (idle/staging). You deploy the new backend application version to Green, test it, and then instantly switch traffic over at the load balancer (NGINX) level.

**NGINX Role:**
Update the `upstream` block from:
```nginx
upstream app_pool { server blue_app:8080; }
```
To:
```nginx
upstream app_pool { server green_app:8080; }
```
Then run `nginx -s reload`.

### True Rolling Updates with NGINX Plus
*Note: This specific API feature is commercial.* You can use the NGINX Plus API to dynamically add or remove servers from an `upstream` block without even reloading the configuration file, enabling perfect rolling updates in orchestration environments.

## 4. Production-Grade `docker-compose.yml`
A realistic template for deploying a reverse proxy in production.

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:1.25-alpine
    container_name: production_proxy
    restart: always # Or unless-stopped
    ports:
      - "80:80"
      - "443:443"
    environment:
      - TZ=UTC
    ulimits:
      nofile: # Maximum open file descriptors!
        soft: 65536
        hard: 65536
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    networks:
      - proxy_net

networks:
  proxy_net:
    driver: bridge
```
*Why `ulimits`?* By default, Docker containers have a limit of 1024 open file descriptors. A high-traffic NGINX server needs thousands (`worker_connections`).

## 5. Security Architecture Best Practices
1. **Hide NGINX Version**: Prevent attackers from knowing exactly which CVEs your server might be vulnerable to by adding `server_tokens off;` in the `http` block.
2. **Buffer Overflows Mitigation**: Prevent enormous, malicious headers or payloads.
    ```nginx
    client_body_buffer_size  10K;
    client_header_buffer_size 1k;
    client_max_body_size 8m; # Essential for file upload controls
    large_client_header_buffers 2 1k;
    ```
3. **Timeouts**: Drop idle or slow clients (Slowloris attacks).
    ```nginx
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;
    ```
4. **WAF (Web Application Firewall)**: In highly secure environments, compile NGINX with ModSecurity to inspect layer 7 traffic against OWASP Core Rule Sets.

## 6. Real-world Troubleshooting Steps
When an alert fires in production:
1. **Understand Symptoms**: Is it slow? 5xx errors? 4xx errors? Total outage?
2. **Check NGINX Access Logs**: See if traffic is arriving and what HTTP status is being returned. Are `$upstream_response_time` values high?
3. **Check Error Logs**: Look natively in `/var/log/nginx/error.log`. Look for "Connection refused", "No route to host", or "worker_connections are not enough".
4. **Test Configuration**: If someone just deployed, run `nginx -t` to test syntax immediately.
5. **Check the OS**: Is the server out of RAM? Is the disk 100% full (often caused by massive unrotated logs)? 

## 7. Interview Preparation (Level 7)

1. **How do you safely apply a new configuration to a running NGINX server serving millions of active connections?**
   *Answer:* You run `nginx -s reload`. The master process will verify syntax, spawn new workers with the new config, and signal old workers to finish their current connections and exit gracefully.

2. **What does `server_tokens off;` do and why use it?**
   *Answer:* It prevents NGINX from broadcasting its specific version number (e.g. `Server: nginx/1.25.1`) in HTTP responses and default error pages. It is a security by obscurity best practice to prevent automated vulnerability scanners.

3. **In a Docker Compose environment, why might you need to explicitly define `ulimits nofile` for the NGINX service?**
   *Answer:* Docker typically inherits default limits from the host OS system (often 1024 open files). Since an NGINX worker needs one file descriptor for the client and one for the backend proxy connection, the default limit is quickly exhausted under moderate traffic. Elevating `nofile` allows high concurrency.
