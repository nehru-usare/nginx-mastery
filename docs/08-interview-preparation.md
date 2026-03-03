# Level 8: Interview Preparation

## 1. Beginner Questions
1. **What is NGINX?**
   *Answer:* A high-performance, open-source web server, reverse proxy, load balancer, and HTTP cache. It uses an asynchronous, event-driven architecture rather than creating new threads for each request, making it extremely memory efficient under high concurrency.
   
2. **What is the difference between a Reverse Proxy and a Forward Proxy?**
   *Answer:* A forward proxy protects the client (hiding the client's IP from the internet). A reverse proxy protects the server (hiding the backend origin servers from the client) and handles TLS termination, load balancing, and caching.

3. **Where is the primary configuration file located by default?**
   *Answer:* `/etc/nginx/nginx.conf`.

4. **What command is used to test an NGINX configuration without restarting the server?**
   *Answer:* `nginx -t`

## 2. Intermediate Questions
1. **Explain the difference between `worker_processes` and `worker_connections`.**
   *Answer:* `worker_processes` determines how many OS-level processes NGINX spins up (usually 1 per CPU core). `worker_connections` dictates how many concurrent connections each individual worker process can hold concurrently inside its event loop.

2. **In a `location` block, what does the trailing slash in `proxy_pass http://backend/` do?**
   *Answer:* The trailing slash modifies the URI. It strips the path prefix matched by the `location` directive before passing the request to the upstream server. Without the slash, the full original URI is appended.

3. **How does NGINX handle default load balancing?**
   *Answer:* By default inside an `upstream` block, NGINX uses a Round Robin algorithm, sending sequential requests to each server in the pool evenly.

4. **What is SSL Termination?**
   *Answer:* It is the process where NGINX decrypts incoming HTTPS traffic at the proxy layer and passes unencrypted HTTP traffic to the backend server over the private network, offloading CPU-intensive crypto operations from application servers.

## 3. Advanced Production Questions
1. **How do you apply a new configuration without dropping active client connections?**
   *Answer:* By using `nginx -s reload`. The master process validates the syntax, spins up new workers using the new config, and signals the old workers to stop accepting new requests and exit once their current connections finish (Graceful Restart).

2. **What are the `$remote_addr`, `$http_x_forwarded_for`, and `real_ip` modules used for?**
   *Answer:* Usually, `$remote_addr` captures the IP of the physical connection (e.g., an AWS ALB or Cloudflare). To log or rate-limit the true client IP, NGINX must read the `X-Forwarded-For` header using the `real_ip` module's `set_real_ip_from` directive to explicitly trust the load balancer's IPs.

3. **Explain Microcaching and its use case.**
   *Answer:* Microcaching is caching dynamically generated content (like an API response or WordPress homepage) for a very short period (e.g., 1 second). It drastically protects backend SQL databases from sudden traffic spikes (Slashdot effect) while ensuring content is never noticeably stale.

4. **Why would you disable proxy buffering?**
   *Answer:* Proxy buffering saves backend connection time by allowing NGINX to buffer the entire response into memory/disk before sending it to the slow client. However, you disable it (`proxy_buffering off;`) for persistent connections where data must stream instantly, such as Long Polling, Server-Sent Events (SSE), or WebSockets.

## 4. Scenario-Based Troubleshooting
**Scenario 1: You are getting a "502 Bad Gateway" error. What steps do you take?**
*Answer:* A 502 means NGINX cannot communicate with the upstream server. 
1. Check the NGINX `error.log`.
2. Verify if the backend application is running.
3. Verify if NGINX is proxying to the right port (`http://localhost:3000` vs `8080`).
4. Look for SELinux blocking network connections (`setsebool -P httpd_can_network_connect 1`).

**Scenario 2: You receive a "403 Forbidden" on a static HTML site.**
*Answer:* This is almost always a permissions issue.
1. Check if the `index.html` file actually exists in the `root` directive path.
2. Verify that the NGINX worker user (e.g., `nginx` or `www-data`) has read (`r`) and execute (`x`) permissions on the directory path and the files.

**Scenario 3: Users report that client IPs in the backend app all show as `127.0.0.1` or the Docker Gateway IP.**
*Answer:* NGINX is not forwarding the client IP headers. You need to add:
```nginx
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```
to the `location` block handling the `proxy_pass`.

## 5. System Design Questions
**Design an API Gateway architecture for a microservice platform using NGINX.**
*Answer Outline:*
- Place NGINX as the public edge proxy terminating SSL (`listen 443 ssl http2;`).
- Use path-based routing (`location /api/users/`, `location /api/orders/`) to route to different internal Docker/Kubernetes services.
- Implement global rate limiting (`limit_req_zone`) to protect against DDoS.
- Standardize security headers (`HSTS`, `X-Frame-Options`) in the root `http` or `server` block.
- Pass `X-Correlation-ID` or `X-Request-ID` headers to trace requests across microservices.
- Export metrics using `stub_status` to Prometheus for observability.
