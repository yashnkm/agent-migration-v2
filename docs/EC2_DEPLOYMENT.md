# EC2 Deployment Guide

Complete step-by-step guide for deploying the Java Codebase Analyzer on AWS EC2.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [EC2 Instance Setup](#ec2-instance-setup)
3. [Application Deployment](#application-deployment)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Process Management](#process-management)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Security Best Practices](#security-best-practices)

---

## Prerequisites

### AWS Requirements
- AWS Account with EC2 access
- EC2 key pair (.pem file)
- Basic knowledge of SSH and Linux commands

### Recommended Instance Type
- **Minimum**: t2.micro (1GB RAM, 1 vCPU) - Free tier eligible
- **Recommended**: t2.small (2GB RAM, 1 vCPU) - Better performance
- **For large repos**: t2.medium (4GB RAM, 2 vCPUs)

### Operating System
- Ubuntu 20.04 LTS (recommended)
- Ubuntu 22.04 LTS
- Amazon Linux 2

---

## EC2 Instance Setup

### Step 1: Launch EC2 Instance

1. **Go to EC2 Console**
   - Navigate to: https://console.aws.amazon.com/ec2

2. **Launch Instance**
   - Click "Launch Instance"

3. **Configure Instance**:
   ```
   Name: java-codebase-analyzer
   AMI: Ubuntu Server 20.04 LTS (HVM), SSD Volume Type
   Instance Type: t2.small (or t2.micro for testing)
   Key Pair: Select existing or create new
   ```

4. **Configure Storage**:
   ```
   Size: 20 GB (minimum)
   Volume Type: General Purpose SSD (gp2)
   ```

   Note: Cloned repositories are stored in `/tmp` which is cleared on reboot

5. **Configure Security Group**:
   ```
   Rule 1 - SSH:
     Type: SSH
     Protocol: TCP
     Port: 22
     Source: Your IP (or 0.0.0.0/0)

   Rule 2 - Streamlit:
     Type: Custom TCP
     Protocol: TCP
     Port: 8051
     Source: 0.0.0.0/0 (or specific IPs)
   ```

6. **Launch Instance**
   - Review settings and click "Launch"
   - Wait for instance state to become "Running"
   - Note the Public IPv4 address

### Step 2: Connect to Instance

```bash
# Make key file read-only (required)
chmod 400 your-key.pem

# Connect via SSH
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>

# Example:
# ssh -i my-key.pem ubuntu@54.123.45.67
```

---

## Application Deployment

### Step 1: Update System

```bash
# Update package lists
sudo apt update

# Upgrade installed packages (optional but recommended)
sudo apt upgrade -y
```

### Step 2: Install Dependencies

```bash
# Install Python 3, pip, and virtual environment
sudo apt install python3 python3-pip python3-venv -y

# Install Git
sudo apt install git -y

# Install build tools (required for tree-sitter)
sudo apt install build-essential -y

# Verify installations
python3 --version  # Should show Python 3.8+
pip3 --version
git --version
```

### Step 3: Clone Repository

**Option A: From GitHub (if your repo is on GitHub)**
```bash
# Navigate to home directory
cd ~

# Clone repository
git clone https://github.com/your-username/agent-migration-v2.git

# Navigate to project
cd agent-migration-v2
```

**Option B: Upload from Local Machine (using SCP)**
```bash
# From your local machine (not EC2):
# Upload entire project folder
scp -i your-key.pem -r "/path/to/agent-migration-v2" ubuntu@<EC2-IP>:~

# Then SSH into EC2:
ssh -i your-key.pem ubuntu@<EC2-IP>
cd ~/agent-migration-v2
```

### Step 4: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv)
```

### Step 5: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This will take 5-10 minutes
# Watch for any errors
```

**Common Installation Issues**:

If PyTorch installation fails:
```bash
# Install PyTorch separately
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
```

If tree-sitter build fails:
```bash
# Ensure build tools are installed
sudo apt install build-essential python3-dev -y
```

---

## Configuration

### Step 1: Environment Variables

```bash
# Create .env file
nano .env
```

Add the following content:
```bash
# Required: Your Gemini API Key
CODEBASE_GEMINI_KEY=your_actual_gemini_api_key_here

# Optional: Specify model (default: gemini-2.0-flash-exp)
CODEBASE_GEMINI_MODEL=gemini-2.0-flash-exp
```

**Get Gemini API Key**:
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy and paste into `.env` file

Save and exit (Ctrl+X, then Y, then Enter)

### Step 2: Verify Configuration

```bash
# Check if .env file exists
cat .env

# Should display your configuration (key will be hidden in actual usage)
```

### Step 3: Streamlit Port Configuration

The port is already configured in `.streamlit/config.toml` (port 8051).

To verify:
```bash
cat .streamlit/config.toml
```

Should show:
```toml
[server]
port = 8051
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false
```

---

## Running the Application

### Option 1: Quick Test (Foreground)

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run application
streamlit run app_v2.py

# You should see:
# You can now view your Streamlit app in your browser.
# Network URL: http://<private-ip>:8051
# External URL: http://<public-ip>:8051
```

**Access the application**:
- Open browser: `http://<EC2-PUBLIC-IP>:8051`
- You should see the Java Codebase Analyzer interface

**Stop the application**: Press Ctrl+C

### Option 2: Background Process (Simple)

```bash
# Run in background with nohup
nohup streamlit run app_v2.py > app.log 2>&1 &

# Get process ID
echo $!  # Note this number

# View logs
tail -f app.log

# Stop background process (when needed)
kill <process-id>
```

### Option 3: Screen Session (Recommended for Testing)

```bash
# Install screen (if not installed)
sudo apt install screen -y

# Start screen session
screen -S java-analyzer

# Inside screen, activate venv and run app
source venv/bin/activate
streamlit run app_v2.py

# Detach from screen: Press Ctrl+A, then D

# Reattach to screen
screen -r java-analyzer

# List all screen sessions
screen -ls

# Kill screen session
screen -X -S java-analyzer quit
```

---

## Process Management

### Using systemd (Production Recommended)

Create a systemd service for automatic startup and management.

#### Step 1: Create Service File

```bash
sudo nano /etc/systemd/system/java-analyzer.service
```

Add the following content:
```ini
[Unit]
Description=Java Codebase Analyzer - Streamlit Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/agent-migration-v2
Environment="PATH=/home/ubuntu/agent-migration-v2/venv/bin"
ExecStart=/home/ubuntu/agent-migration-v2/venv/bin/streamlit run app_v2.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Important**: Update paths if your project is in a different location.

#### Step 2: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable java-analyzer

# Start service
sudo systemctl start java-analyzer

# Check status
sudo systemctl status java-analyzer
```

You should see:
```
● java-analyzer.service - Java Codebase Analyzer
   Loaded: loaded
   Active: active (running)
```

#### Step 3: Manage Service

```bash
# Stop service
sudo systemctl stop java-analyzer

# Restart service
sudo systemctl restart java-analyzer

# View logs
sudo journalctl -u java-analyzer -f

# View last 100 lines
sudo journalctl -u java-analyzer -n 100
```

---

## Monitoring & Maintenance

### Check Application Status

```bash
# Check if application is running
ps aux | grep streamlit

# Check port 8051 is listening
sudo netstat -tlnp | grep 8051
# or
sudo lsof -i :8051
```

### Monitor System Resources

```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top
# Press 'q' to exit

# Monitor in real-time
htop  # Install with: sudo apt install htop -y
```

### Monitor Application Logs

**With systemd**:
```bash
# Live tail
sudo journalctl -u java-analyzer -f

# Last 50 lines
sudo journalctl -u java-analyzer -n 50

# Today's logs
sudo journalctl -u java-analyzer --since today
```

**With nohup**:
```bash
tail -f app.log
```

### Clean Up Temporary Files

Cloned repositories are stored in `/tmp/codebase_analysis/`:

```bash
# Check size
du -sh /tmp/codebase_analysis/

# List contents
ls -lah /tmp/codebase_analysis/

# Clean up all cloned repos
rm -rf /tmp/codebase_analysis/*

# Note: /tmp is automatically cleared on system reboot
```

### Update Application

```bash
# Navigate to project
cd ~/agent-migration-v2

# Pull latest changes (if using Git)
git pull

# Activate virtual environment
source venv/bin/activate

# Update dependencies (if requirements.txt changed)
pip install -r requirements.txt --upgrade

# Restart application
# If using systemd:
sudo systemctl restart java-analyzer

# If using nohup or screen:
# Stop old process and start new one
```

---

## Troubleshooting

### Issue 1: Cannot Access Application

**Symptom**: Browser shows "Connection timed out" or "Cannot reach"

**Solutions**:

1. **Check Security Group**:
   ```
   AWS Console → EC2 → Security Groups
   → Ensure port 8051 is open (0.0.0.0/0)
   ```

2. **Check Application is Running**:
   ```bash
   sudo systemctl status java-analyzer
   # or
   ps aux | grep streamlit
   ```

3. **Check Port is Listening**:
   ```bash
   sudo netstat -tlnp | grep 8051
   ```

4. **Check Firewall** (Ubuntu UFW):
   ```bash
   sudo ufw status
   # If active, allow port:
   sudo ufw allow 8051
   ```

### Issue 2: Application Crashed

**Check Logs**:
```bash
sudo journalctl -u java-analyzer -n 100
```

**Common Causes**:
- Out of memory (upgrade instance type)
- Missing API key (check .env file)
- Python dependencies missing (reinstall requirements.txt)

**Restart**:
```bash
sudo systemctl restart java-analyzer
```

### Issue 3: Out of Memory

**Symptom**: Process killed, "Killed" message in logs

**Solutions**:

1. **Check Memory**:
   ```bash
   free -h
   ```

2. **Upgrade Instance**:
   - t2.micro (1GB) → t2.small (2GB)
   - In EC2 Console: Stop instance → Change instance type → Start

3. **Add Swap Space** (temporary solution):
   ```bash
   # Create 2GB swap file
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile

   # Make permanent (add to /etc/fstab)
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

### Issue 4: Gemini API Quota Exceeded

**Symptom**: "Resource exhausted: Quota exceeded" error

**Solution**: Use local embeddings
- In Streamlit UI, check "Use Local Embeddings (offline)"
- Or wait for quota to reset (next day)

### Issue 5: Git Clone Fails

**Symptom**: Cannot clone repositories in the application

**Check**:
```bash
# Test internet connectivity
ping -c 4 8.8.8.8

# Test DNS
nslookup github.com

# Test GitHub access
curl -I https://github.com

# Check Git is installed
git --version
```

**Solution**:
```bash
# Reinstall git if needed
sudo apt install git -y
```

### Issue 6: Python Module Not Found

**Symptom**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Restart application
sudo systemctl restart java-analyzer
```

---

## Security Best Practices

### 1. Restrict SSH Access

```bash
# Edit security group to allow SSH only from your IP
# AWS Console → EC2 → Security Groups → Edit Inbound Rules
# Change SSH source from 0.0.0.0/0 to Your IP
```

### 2. Keep System Updated

```bash
# Regular updates
sudo apt update
sudo apt upgrade -y

# Enable automatic security updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. Use IAM Roles (Instead of Access Keys)

If accessing other AWS services, use IAM roles instead of storing credentials.

### 4. Protect .env File

```bash
# Ensure .env is not world-readable
chmod 600 .env

# Verify
ls -la .env
# Should show: -rw------- (only owner can read/write)
```

### 5. Use HTTPS (Optional)

For production, consider setting up HTTPS:
- Use AWS Application Load Balancer with SSL certificate
- Or use nginx as reverse proxy with Let's Encrypt

### 6. Limit Application Access

If not public-facing:
```bash
# Restrict port 8051 to specific IPs in Security Group
# Change source from 0.0.0.0/0 to specific IP ranges
```

---

## Cost Optimization

### EC2 Instance Costs (US East Region)

| Instance Type | vCPU | RAM | Price/Month* |
|--------------|------|-----|--------------|
| t2.micro | 1 | 1GB | ~$8.50 (Free tier: 750 hrs/month) |
| t2.small | 1 | 2GB | ~$17.00 |
| t2.medium | 2 | 4GB | ~$34.00 |

*Prices approximate, check AWS pricing for your region

### Tips to Reduce Costs

1. **Use Free Tier**: t2.micro for first 12 months
2. **Stop When Not in Use**: Stop instance when not needed
3. **Use Spot Instances**: 70-90% cheaper (for dev/test)
4. **Right-Size Instance**: Don't over-provision
5. **Delete Unused Volumes**: Remove unused EBS volumes

### Stop/Start Instance

```bash
# Stop instance (keeps data, stops billing for compute)
# AWS Console → EC2 → Instances → Select instance → Instance State → Stop

# Start instance
# Instance State → Start

# Note: Public IP may change unless you use Elastic IP
```

---

## Backup & Restore

### Backup Application

```bash
# Backup entire project folder
cd ~
tar -czf java-analyzer-backup-$(date +%Y%m%d).tar.gz agent-migration-v2

# Download to local machine
# From your local machine:
scp -i your-key.pem ubuntu@<EC2-IP>:~/java-analyzer-backup-*.tar.gz .
```

### Create AMI (Amazon Machine Image)

1. **AWS Console → EC2 → Instances**
2. Select your instance
3. **Actions → Image and templates → Create image**
4. Name: `java-analyzer-v1`
5. Click "Create image"

Now you can launch new instances from this AMI with everything pre-installed.

---

## Performance Tuning

### For Large Repositories

1. **Increase Instance Size**: Use t2.medium or larger
2. **Increase Storage**: If analyzing multiple large repos
3. **Monitor Resources**: Use CloudWatch for monitoring

### Streamlit Configuration

Edit `.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 200  # Max file upload size in MB
maxMessageSize = 200  # Max message size in MB

[browser]
gatherUsageStats = false  # Disable telemetry
```

---

## Quick Reference Commands

```bash
# Connect to EC2
ssh -i your-key.pem ubuntu@<EC2-IP>

# Navigate to project
cd ~/agent-migration-v2

# Activate virtual environment
source venv/bin/activate

# Start application (systemd)
sudo systemctl start java-analyzer

# Check status
sudo systemctl status java-analyzer

# View logs
sudo journalctl -u java-analyzer -f

# Restart application
sudo systemctl restart java-analyzer

# Stop application
sudo systemctl stop java-analyzer

# Check disk space
df -h

# Check memory
free -h

# Clean temp files
rm -rf /tmp/codebase_analysis/*

# Update application
git pull
pip install -r requirements.txt --upgrade
sudo systemctl restart java-analyzer
```

---

## Next Steps

After successful deployment:

1. **Test the application**: Analyze a sample repository
2. **Set up monitoring**: Configure CloudWatch alarms
3. **Create backup**: Take an AMI snapshot
4. **Document**: Note down public IP and access details
5. **Share**: Give access to team members

---

**Last Updated**: November 2025
**Author**: Capgemini Discovery Agent Team
