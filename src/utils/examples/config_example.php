<?php
/**
 * config_example.php
 * 
 * Example configuration file for MI Chatbots LAMP utilities.
 * Copy this file to config.php and customize for your environment.
 * 
 * @package MIChatbots
 */

return [
    // Database Configuration
    'database' => [
        'host' => $_ENV['DB_HOST'] ?? 'localhost',
        'port' => $_ENV['DB_PORT'] ?? '3306',
        'dbname' => $_ENV['DB_NAME'] ?? 'mi_chatbots',
        'username' => $_ENV['DB_USER'] ?? 'mi_app',
        'password' => $_ENV['DB_PASS'] ?? '',
        'charset' => 'utf8mb4',
        'options' => [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
            PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci"
        ]
    ],
    
    // Logging Configuration
    'logging' => [
        'level' => $_ENV['LOG_LEVEL'] ?? 'INFO', // DEBUG, INFO, WARNING, ERROR, CRITICAL
        'file_path' => $_ENV['LOG_PATH'] ?? '/var/log/mi_chatbots/app.log',
        'database_logging' => true,
        'file_logging' => true,
        'max_log_file_size' => '10M',
        'rotate_logs' => true
    ],
    
    // PDF Generation Configuration
    'pdf' => [
        'temp_dir' => $_ENV['PDF_TEMP_DIR'] ?? '/tmp/mi_pdfs',
        'font_dir' => $_ENV['PDF_FONT_DIR'] ?? null,
        'enable_remote' => false, // Security: disable remote resources
        'memory_limit' => '256M',
        'timeout_seconds' => 30,
        'dpi' => 96,
        'default_paper_size' => 'A4',
        'default_orientation' => 'portrait'
    ],
    
    // Session Management Configuration
    'session' => [
        'cleanup_days' => 90, // Days to keep old sessions
        'max_message_length' => 5000,
        'max_messages_per_session' => 500,
        'session_timeout_hours' => 24,
        'auto_complete_inactive_hours' => 6
    ],
    
    // Security Configuration
    'security' => [
        'allowed_origins' => [
            'https://hpvmiapp.streamlit.app',
            'https://ohimiapp.streamlit.app',
            'http://localhost:8501', // Streamlit default
            'http://127.0.0.1:8501'
        ],
        'api_rate_limit' => [
            'requests_per_minute' => 60,
            'requests_per_hour' => 1000
        ],
        'max_student_name_length' => 255,
        'max_feedback_length' => 50000
    ],
    
    // Performance Configuration
    'performance' => [
        'enable_caching' => false, // Set to true if using Redis/Memcached
        'cache_ttl_seconds' => 300,
        'database_connection_pool_size' => 10,
        'memory_limit' => '512M',
        'max_execution_time' => 300 // 5 minutes
    ],
    
    // Feature Flags
    'features' => [
        'enable_pdf_generation' => true,
        'enable_database_logging' => true,
        'enable_performance_monitoring' => true,
        'enable_session_cleanup' => true,
        'enable_health_checks' => true
    ],
    
    // Application Settings
    'app' => [
        'name' => 'MI Chatbots System',
        'version' => '1.0.0',
        'environment' => $_ENV['APP_ENV'] ?? 'production', // development, staging, production
        'debug' => $_ENV['APP_DEBUG'] ?? false,
        'timezone' => $_ENV['APP_TIMEZONE'] ?? 'UTC'
    ],
    
    // Email Configuration (for notifications)
    'email' => [
        'enabled' => false,
        'smtp_host' => $_ENV['SMTP_HOST'] ?? '',
        'smtp_port' => $_ENV['SMTP_PORT'] ?? 587,
        'smtp_username' => $_ENV['SMTP_USER'] ?? '',
        'smtp_password' => $_ENV['SMTP_PASS'] ?? '',
        'from_email' => $_ENV['FROM_EMAIL'] ?? 'noreply@example.com',
        'from_name' => 'MI Chatbots System'
    ],
    
    // External Services
    'services' => [
        'groq_api_key' => $_ENV['GROQ_API_KEY'] ?? '',
        'openai_api_key' => $_ENV['OPENAI_API_KEY'] ?? '',
        'backup_service_url' => $_ENV['BACKUP_SERVICE_URL'] ?? null
    ]
];
?>