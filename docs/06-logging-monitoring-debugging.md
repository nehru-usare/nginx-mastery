# Level 6: Logging, Monitoring & Debugging

## 1. Access Log (`access_log`)
The `access_log` records information about every single client request that reaches NGINX. By default, it uses the `combined` format.

```nginx
http {
    # Default location and format
    access_log /var/log/nginx/access.log combined;
    
    server {
        listen 80;
        # You can override access_log per server or location block
        access_log /var/log/nginx/api_access.log;
        
        # Or disable access logging entirely for static assets to save I/O
        location /images/ {
            access_log off;
        }
    }
}
```

## 2. Error Log (`error_log`)
The `error_log` records diagnostic information. It helps identify crashes, permission issues, or configuration syntax errors.

It takes a severity level: `debug`, `info`, `notice`, `warn`, `error`, `crit`, `alert`, or `emerg`.

```nginx
http {
    # Only log errors, critical, alerts, and emergencies
    error_log /var/log/nginx/error.log error;
}
```

## 3. Custom Log Formats
By defining a `log_format`, you can output JSON logs (highly recommended for centralized logging systems like ELK or Datadog) or append custom headers.

```nginx
http {
    # Creating a JSON format
    log_format json_combined escape=json
    '{'
      '"time_local":"$time_local",'
      '"remote_addr":"$remote_addr",'
      '"remote_user":"$remote_user",'
      '"request":"$request",'
      '"status": "$status",'
      '"body_bytes_sent":"$body_bytes_sent",'
      '"request_time":"$request_time",'
      '"http_referrer":"$http_referer",'
      '"http_user_agent":"$http_user_agent",'
      '"upstream_response_time":"$upstream_response_time",'
      '"upstream_addr":"$upstream_addr"'
    '}';

    # Applying the custom format
    access_log /var/log/nginx/access-json.log json_combined;
}
```

## 4. Debug Mode
If you are struggling with complex rewrite rules, proxy buffering, or SSL handshakes, NGINX provides a highly verbose `debug` mode.

*Requirement: Your NGINX binary must be compiled with `--with-debug`.* (The official NGINX docker images usually include this).

```nginx
# Notice this is in the main context, not inside http {}
error_log /var/log/nginx/error.log debug;
```
*Warning: `debug` mode dumps massive amounts of data. Never leave it on in production!*

## 5. Real IP Handling
When NGINX is behind an AWS ALB, Cloudflare, or another reverse proxy, `$remote_addr` will show the internal Load Balancer's IP instead of the original client's IP.

To fix this, use the `real_ip` module (must be compiled with `--with-http_realip_module`):

```nginx
http {
    # Trust the IP ranges of the Load Balancer (e.g., Cloudflare IPs)
    set_real_ip_from 10.0.0.0/8;
    set_real_ip_from 173.245.48.0/20; # Example Cloudflare IP
    
    # Read the true client IP from this header
    real_ip_header X-Forwarded-For;
    
    # Recursively remove trusted IPs from X-Forwarded-For
    real_ip_recursive on;
}
```

## 6. Prometheus Integration (Observability)
To get deep metrics (active connections, reading/writing states, total handled requests), NGINX has a `stub_status` module.

```nginx
server {
    listen 80;
    server_name localhost;

    location /nginx_status {
        # Enable basic status pages
        stub_status;
        
        # Only allow local network (e.g., Prometheus scraper)
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }
}
```

**Architecture Concept:**
1. You expose `/nginx_status`.
2. You run an **NGINX Prometheus Exporter** container alongside NGINX.
3. The Exporter constantly polls `/nginx_status` and translates the data into Prometheus metrics format on port `9113`.
4. Prometheus scrapes port `9113`.
5. Grafana visualizes the Prometheus data (dashboards showing connections, RPS).

*(Note: NGINX Plus offers a much richer `/api/` endpoint delivering highly granular upstream metrics).*

## 7. Observability Best Practices
- **Standardize on JSON**: `log_format escape=json` makes logs instantly readable by Fluentd/Logstash.
- **Log Upstream Metrics**: Always include `$upstream_response_time` and `$upstream_cache_status`. It helps you immediately prove whether slowness is your backend application or NGINX itself.
- **Buffer Logs in High Traffic**: Under massive load, constantly writing to disk slows NGINX down. 
    ```nginx
    access_log /var/log/nginx/access.log combined buffer=16k flush=2s;
    ```
    *(Writes memory buffer to disk only when it reaches 16KB or 2 seconds have passed).*

## 8. Interview Preparation (Level 6)

1. **How do you find out if a request was delayed by NGINX or the backend application?**
   *Answer:* Check the custom access log. Compare `$request_time` (the total time NGINX spent on the request) versus `$upstream_response_time` (the time it took the backend to send its response). If the backend time is negligible but request time is high, the client is slow. If both are high, the backend is struggling.

2. **Why is `$remote_addr` logging the IP of my load balancer instead of my users?**
   *Answer:* Because the connection to NGINX is physically originating from the load balancer. You must use the `ngx_http_realip_module` and `set_real_ip_from` directives to tell NGINX to extract the real IP from the `X-Forwarded-For` header.

3. **What is `stub_status`?**
   *Answer:* It's an NGINX module that provides a simple web page showing real-time metrics, such as the total number of accepted connections and current active reading/writing/waiting states. It is commonly scraped by monitoring agents like Datadog or Prometheus.

4. **Why is logging JSON better than the default combined format?**
   *Answer:* JSON provides highly structured key-value pairs. Standard log aggregators (ELK, Datadog, Splunk) can natively parse JSON without requiring you to write complex, fragile Regex (`grok`) patterns.
