# LAMP-Stack Deployment Guide for MI Chatbots

This guide will help you deploy the MI Chatbots system with LAMP-stack PHP utilities in various environments.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Local Development Setup](#local-development-setup)
3. [Shared Hosting Deployment](#shared-hosting-deployment)
4. [VPS/Cloud Server Deployment](#vpscloud-server-deployment)
5. [Integration with Existing Apps](#integration-with-existing-apps)
6. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- PHP 7.4+ with MySQL/PDO support
- MySQL 5.7+ or MariaDB 10.2+
- Web server (Apache/Nginx)
- Composer (for PDF generation)

### 5-Minute Setup

1. **Clone the repository:**
```bash
git clone https://github.com/manirathnam2001/ManiUMN-MI_chatbots.git
cd ManiUMN-MI_chatbots
```

2. **Set up the database:**
```bash
mysql -u root -p -e "CREATE DATABASE mi_chatbots CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p mi_chatbots < database/mi_sessions.sql
```

3. **Install PHP dependencies:**
```bash
cd src/utils
composer install
```

4. **Configure the system:**
```bash
cp examples/config_example.php config.php
# Edit config.php with your database credentials
```

5. **Test the installation:**
```bash
php examples/test_utilities.php
```

## Local Development Setup

### Using XAMPP (Windows/Mac/Linux)

1. **Install XAMPP:**
   - Download from [https://www.apachefriends.org/](https://www.apachefriends.org/)
   - Install with Apache, MySQL, and PHP

2. **Setup the project:**
```bash
# Copy project to XAMPP htdocs
cp -r ManiUMN-MI_chatbots /path/to/xampp/htdocs/

# Start XAMPP services
sudo /opt/lampp/lampp start
```

3. **Create database:**
   - Open phpMyAdmin: http://localhost/phpmyadmin
   - Create database `mi_chatbots`
   - Import `database/mi_sessions.sql`

4. **Configure PHP:**
```bash
cd /path/to/xampp/htdocs/ManiUMN-MI_chatbots/src/utils
composer install
cp examples/config_example.php config.php
```

5. **Test setup:**
   - Visit: http://localhost/ManiUMN-MI_chatbots/src/utils/examples/test_utilities.php

### Using Docker (Recommended for Development)

1. **Create docker-compose.yml:**
```yaml
version: '3.8'
services:
  web:
    image: php:8.1-apache
    ports:
      - "8080:80"
    volumes:
      - ./:/var/www/html
    depends_on:
      - db
    environment:
      - DB_HOST=db
      - DB_NAME=mi_chatbots
      - DB_USER=root
      - DB_PASS=rootpassword

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: mi_chatbots
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database/mi_sessions.sql:/docker-entrypoint-initdb.d/mi_sessions.sql

volumes:
  mysql_data:
```

2. **Start the environment:**
```bash
docker-compose up -d
```

3. **Install dependencies:**
```bash
docker-compose exec web bash
cd /var/www/html/src/utils
composer install
```

## Shared Hosting Deployment

### cPanel/Shared Hosting Setup

1. **Upload files:**
   - Upload the entire project to your hosting account
   - Place PHP files in `public_html` or subdirectory

2. **Create database:**
   - Use cPanel MySQL Databases
   - Create database: `yourdomain_mi_chatbots`
   - Create user with full privileges
   - Import schema using phpMyAdmin

3. **Configure environment:**
```php
// config.php
<?php
return [
    'database' => [
        'host' => 'localhost',
        'dbname' => 'yourdomain_mi_chatbots',
        'username' => 'yourdomain_miuser',
        'password' => 'your_secure_password'
    ],
    'logging' => [
        'file_path' => '/home/yourdomain/logs/mi_chatbots.log'
    ]
];
?>
```

4. **Set up Composer (if available):**
```bash
# If Composer is available on shared hosting
cd public_html/mi_chatbots/src/utils
composer install

# If Composer is not available, upload vendor folder manually
```

5. **Set permissions:**
```bash
chmod 755 src/utils/examples/
chmod 644 src/utils/*.php
chmod 600 config.php
```

### Integration with Streamlit Cloud

1. **Deploy PHP backend to shared hosting**
2. **Update Streamlit app environment variables:**
```python
# In your Streamlit app
import os
PHP_BACKEND_URL = os.getenv('PHP_BACKEND_URL', 'https://yoursite.com/mi_chatbots/src/utils/examples/mi_bot_integration.php')
```

3. **Configure CORS for cross-origin requests:**
```php
// In mi_bot_integration.php
header('Access-Control-Allow-Origin: https://yourapp.streamlit.app');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
```

## VPS/Cloud Server Deployment

### Ubuntu/Debian Server Setup

1. **Install LAMP stack:**
```bash
sudo apt update
sudo apt install apache2 mysql-server php php-mysql php-mbstring php-xml php-zip composer

# Secure MySQL
sudo mysql_secure_installation
```

2. **Configure Apache:**
```bash
sudo a2enmod rewrite
sudo systemctl restart apache2

# Create virtual host (optional)
sudo nano /etc/apache2/sites-available/mi-chatbots.conf
```

3. **Deploy application:**
```bash
cd /var/www/html
sudo git clone https://github.com/manirathnam2001/ManiUMN-MI_chatbots.git
sudo chown -R www-data:www-data ManiUMN-MI_chatbots
sudo chmod -R 755 ManiUMN-MI_chatbots
```

4. **Set up database:**
```bash
sudo mysql -u root -p
mysql> CREATE DATABASE mi_chatbots CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
mysql> CREATE USER 'mi_app'@'localhost' IDENTIFIED BY 'secure_password';
mysql> GRANT ALL PRIVILEGES ON mi_chatbots.* TO 'mi_app'@'localhost';
mysql> exit

sudo mysql -u root -p mi_chatbots < /var/www/html/ManiUMN-MI_chatbots/database/mi_sessions.sql
```

5. **Install PHP dependencies:**
```bash
cd /var/www/html/ManiUMN-MI_chatbots/src/utils
sudo -u www-data composer install
```

6. **Configure application:**
```bash
sudo cp examples/config_example.php config.php
sudo nano config.php
sudo chown www-data:www-data config.php
sudo chmod 600 config.php
```

### Cloud Platform Deployment

#### AWS EC2

1. **Launch EC2 instance** with Ubuntu 20.04 LTS
2. **Install LAMP stack** (as above)
3. **Configure security groups:**
   - HTTP (80)
   - HTTPS (443)
   - SSH (22)

4. **Set up SSL with Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d yourdomain.com
```

#### Google Cloud Platform

1. **Create Compute Engine instance**
2. **Use startup script:**
```bash
#!/bin/bash
apt update
apt install -y apache2 mysql-server php php-mysql composer git
# ... continue with setup
```

#### DigitalOcean

1. **Use LAMP droplet** (pre-configured)
2. **Deploy application:**
```bash
cd /var/www/html
git clone https://github.com/manirathnam2001/ManiUMN-MI_chatbots.git
# ... continue with configuration
```

## Integration with Existing Apps

### Streamlit Integration

1. **Install Python dependencies:**
```bash
pip install requests streamlit
```

2. **Update existing Streamlit apps:**
```python
# Add to your existing HPV.py or OHI.py
import sys
import os
sys.path.append('src/utils/examples')

try:
    from php_integration import MIPhpIntegration, StreamlitMIIntegration
    PHP_AVAILABLE = True
except ImportError:
    PHP_AVAILABLE = False

# Initialize PHP integration
if PHP_AVAILABLE:
    php_client = MIPhpIntegration("https://yoursite.com/path/to/mi_bot_integration.php")
    st_integration = StreamlitMIIntegration(php_client)
```

3. **Use integrated versions:**
   - Copy `HPV_LAMP_integrated.py` as your new `HPV.py`
   - Copy `OHI_LAMP_integrated.py` as your new `OHI.py`
   - Update the PHP_BACKEND_URL

### WordPress Integration

1. **Create WordPress plugin:**
```php
<?php
/*
Plugin Name: MI Chatbots Integration
Description: Integrates MI Chatbots with WordPress
Version: 1.0
*/

require_once plugin_dir_path(__FILE__) . 'mi_chatbots/src/utils/FeedbackUtils.php';
require_once plugin_dir_path(__FILE__) . 'mi_chatbots/src/utils/SessionStorage.php';

class MIChatbotsPlugin {
    // Plugin implementation
}
```

### Custom Web Application

```php
<?php
// In your existing application
require_once 'path/to/mi_chatbots/src/utils/FeedbackUtils.php';
require_once 'path/to/mi_chatbots/src/utils/SessionStorage.php';

use MIChatbots\Utils\{FeedbackUtils, SessionStorage, Logger};

// Initialize components
$pdo = new PDO(/* your existing database connection */);
$logger = new Logger($pdo);
$storage = new SessionStorage($pdo, $logger);

// Use in your application
$sessionId = $storage->generateSessionId();
$storage->createSession($sessionId, $studentName, $sessionType);
?>
```

## Production Considerations

### Security

1. **Environment variables:**
```bash
# Set in .env file or server environment
export DB_HOST=localhost
export DB_NAME=mi_chatbots
export DB_USER=mi_app
export DB_PASS=secure_password
```

2. **File permissions:**
```bash
# Secure configuration files
chmod 600 config.php
chmod 644 *.php
chmod 755 directories
```

3. **Database security:**
```sql
-- Create dedicated user with minimal privileges
CREATE USER 'mi_app'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON mi_chatbots.* TO 'mi_app'@'localhost';
GRANT EXECUTE ON PROCEDURE mi_chatbots.* TO 'mi_app'@'localhost';
```

### Performance

1. **PHP optimization:**
```ini
; php.ini optimizations
memory_limit = 512M
max_execution_time = 300
opcache.enable = 1
opcache.memory_consumption = 128
```

2. **MySQL optimization:**
```ini
; my.cnf optimizations
innodb_buffer_pool_size = 1G
query_cache_size = 64M
tmp_table_size = 64M
max_heap_table_size = 64M
```

3. **Caching (optional):**
```php
// Redis integration
$redis = new Redis();
$redis->connect('127.0.0.1', 6379);

// Use with CachedSessionStorage
$storage = new CachedSessionStorage($pdo, $logger, $redis);
```

### Monitoring

1. **Set up log rotation:**
```bash
# /etc/logrotate.d/mi-chatbots
/var/log/mi_chatbots/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
}
```

2. **Health monitoring:**
```bash
# Cron job for health checks
*/5 * * * * curl -s http://yoursite.com/mi_chatbots/src/utils/examples/mi_bot_integration.php?action=health_check
```

3. **Automated cleanup:**
```bash
# Weekly cleanup cron job
0 2 * * 0 php /var/www/html/mi_chatbots/cleanup_script.php
```

## Troubleshooting

### Common Issues

1. **Database connection fails:**
```bash
# Check MySQL service
sudo systemctl status mysql

# Test connection
php -r "new PDO('mysql:host=localhost;dbname=mi_chatbots', 'username', 'password');"
```

2. **PDF generation fails:**
```bash
# Install missing extensions
sudo apt install php-gd php-mbstring php-xml

# Check Composer dependencies
composer install --no-dev
```

3. **Permission errors:**
```bash
# Fix file permissions
sudo chown -R www-data:www-data /var/www/html/mi_chatbots
sudo chmod -R 755 /var/www/html/mi_chatbots
sudo chmod 600 config.php
```

4. **CORS issues with Streamlit:**
```php
// Add to mi_bot_integration.php
if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    exit(0);
}
```

### Debug Mode

Enable debug mode for troubleshooting:

```php
// config.php
return [
    'app' => [
        'debug' => true,
        'environment' => 'development'
    ],
    'logging' => [
        'level' => 'DEBUG'
    ]
];
```

### Log Analysis

```bash
# View recent logs
tail -f /var/log/mi_chatbots/app.log

# Search for errors
grep -i error /var/log/mi_chatbots/app.log

# Analyze PHP errors
tail -f /var/log/apache2/error.log
```

## Support

For additional support:

1. Check the [README.md](src/utils/README.md) for detailed API documentation
2. Run the test suite: `php src/utils/examples/test_utilities.php`
3. Review the example integration files in `src/utils/examples/`
4. Check system health: `curl http://yoursite.com/path/to/mi_bot_integration.php?action=health_check`

## Updates and Maintenance

### Updating the System

```bash
# Pull latest changes
git pull origin main

# Update dependencies
composer update

# Run database migrations if any
mysql -u root -p mi_chatbots < database/updates/migration_v1_1.sql

# Test after update
php src/utils/examples/test_utilities.php
```

### Backup Procedures

```bash
# Database backup
mysqldump -u username -p mi_chatbots > backup_$(date +%Y%m%d).sql

# File backup
tar -czf mi_chatbots_backup_$(date +%Y%m%d).tar.gz /var/www/html/mi_chatbots
```

This deployment guide should help you successfully set up the MI Chatbots LAMP utilities in various environments. Adjust the configuration based on your specific hosting environment and requirements.