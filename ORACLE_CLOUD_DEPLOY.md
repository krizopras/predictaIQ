# PredictaIQ — Oracle Cloud Always Free deployment

## 1. Create the VM

Use Oracle Cloud Infrastructure Free Tier and create the VM in your **Home Region**.

Recommended shape:
- Image: Ubuntu 24.04 LTS
- Shape: VM.Standard.A1.Flex (Ampere ARM)
- OCPUs: 2
- Memory: 12 GB
- Boot volume: 50 GB
- Public IPv4: enabled

Oracle's Always Free allowance for Ampere A1 is equivalent to 2 OCPUs and 12 GB RAM for Always Free use. Keep the VM within those limits to avoid paid usage.

## 2. Networking

In the VM's VCN/subnet security rules, allow inbound:
- TCP 22 from your IP (recommended), or temporarily from `0.0.0.0/0`
- TCP 80 from `0.0.0.0/0`
- TCP 443 from `0.0.0.0/0`

Do not expose port 8000 publicly; Gunicorn listens on localhost and Nginx proxies to it.

## 3. Connect over SSH

From Windows PowerShell:

```powershell
ssh -i "C:\path\to\your-key.key" ubuntu@YOUR_PUBLIC_IP
```

## 4. Install system packages

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx
```

## 5. Clone PredictaIQ

```bash
sudo mkdir -p /opt/predictaiq
sudo chown -R ubuntu:ubuntu /opt/predictaiq
cd /opt
rm -rf predictaiq
git clone https://github.com/krizopras/predictaIQ.git predictaiq
cd /opt/predictaiq
```

## 6. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 7. Test the application

```bash
/opt/predictaiq/.venv/bin/gunicorn backend.server:app --bind 127.0.0.1:8000 --workers 2 --threads 2 --timeout 120
```

In a second SSH session:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"service":"PredictaIQ","status":"ok"}
```

Stop the test server with Ctrl+C.

## 8. Install the systemd service

```bash
sudo cp /opt/predictaiq/deploy/predictaiq.service /etc/systemd/system/predictaiq.service
sudo systemctl daemon-reload
sudo systemctl enable --now predictaiq
sudo systemctl status predictaiq --no-pager
```

Logs:

```bash
journalctl -u predictaiq -f
```

## 9. Configure Nginx

```bash
sudo cp /opt/predictaiq/deploy/nginx-predictaiq.conf /etc/nginx/sites-available/predictaiq
sudo ln -sf /etc/nginx/sites-available/predictaiq /etc/nginx/sites-enabled/predictaiq
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

Then visit:

```text
http://YOUR_PUBLIC_IP/health
```

## 10. HTTPS (after adding a domain)

Point an A record such as `predictaiq.example.com` to the VM's public IP. Then run:

```bash
sudo certbot --nginx -d predictaiq.example.com
```

Certbot will configure HTTPS and renewal.

## 11. Updating the application

```bash
cd /opt/predictaiq
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart predictaiq
```

## Important

- Do not put API keys or passwords into GitHub.
- Keep `.env` on the server only.
- The current web service uses the existing JSON data file. Automatic scraping should be added as a separate scheduled process after the web service is stable.
