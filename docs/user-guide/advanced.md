# Advanced Usage

This guide covers advanced Injinja features and patterns for complex configuration scenarios.

## Custom Jinja2 Functions

Injinja supports loading custom Jinja2 filters and tests from Python files.

### Creating Custom Functions

Create `functions.py`:

```python
# functions.py

def filter_to_upper_snake(value):
    """Convert string to UPPER_SNAKE_CASE."""
    return str(value).upper().replace('-', '_').replace(' ', '_')

def filter_safe_filename(value):
    """Convert string to safe filename."""
    import re
    return re.sub(r'[^\w\-_.]', '_', str(value))

def test_is_production(value):
    """Test if environment is production."""
    return str(value).lower() in ['prod', 'production']

def test_has_feature(value, feature):
    """Test if a feature is enabled."""
    features = str(value).lower().split(',')
    return feature.lower() in features
```

### Using Custom Functions

```bash
# Load functions from file
injinja -f functions.py -c config.yml -t template.j2

# Load from multiple files or glob pattern
injinja -f 'functions/*.py' -c config.yml -t template.j2
```

### In Templates

```jinja2
{# template.j2 #}
# Service: {{ app.name | to_upper_snake }}
# Environment: {{ environment }}
# Is Production: {{ environment is is_production }}

{% if features is has_feature('auth') %}
authentication:
  enabled: true
{% endif %}

# Safe filename: {{ app.name | safe_filename }}
```

## Stdin Processing

Injinja can read configuration from stdin, enabling powerful pipeline workflows.

### Basic Stdin Usage

```bash
echo '{"app": {"name": "myapp"}}' | injinja --stdin-format json -t template.j2
```

### Chaining with jq

Extract and transform configuration sections:

```bash
# Extract database config and apply to template
injinja -c 'config/*.yml' -o config-json | \
  jq '.database' | \
  injinja --stdin-format json -t db-migration.sql.j2 -o migration.sql
```

### Complex Pipeline Example

```bash
# Multi-stage processing pipeline
injinja -c 'config/base/*.yml' -c 'config/prod.yml' -o config-json | \
  jq '.microservices[] | select(.enabled == true)' | \
  jq -s '{"services": .}' | \
  injinja --stdin-format json -t kubernetes.yaml.j2 -o deployment.yaml
```

## Validation and Testing

### Output Validation

Compare generated output against expected files:

```bash
# Generate and validate against expected output
injinja -c config.yml -t template.j2 -v expected-output.txt
```

This generates a unified diff showing any differences between generated and expected output.

### Configuration Testing

Test configuration generation with different environments:

```bash
#!/bin/bash
# test-configs.sh

environments=("development" "staging" "production")

for env in "${environments[@]}"; do
  echo "Testing $env configuration..."

  # Generate config
  injinja \
    -e ENVIRONMENT=$env \
    -c "config/base/*.yml" \
    -c "config/environments/$env.yml" \
    -t app.conf.j2 \
    -o "generated/$env.conf"

  # Validate against expected
  if [ -f "expected/$env.conf" ]; then
    injinja \
      -e ENVIRONMENT=$env \
      -c "config/base/*.yml" \
      -c "config/environments/$env.yml" \
      -t app.conf.j2 \
      -v "expected/$env.conf"
  fi
done
```

## Complex Configuration Patterns

### Multi-Environment Matrix

Generate configurations for multiple environments and regions:

```yaml
# matrix-config.yml
environments:
  - name: dev
    region: us-west-2
    replicas: 1
  - name: staging  
    region: us-east-1
    replicas: 2
  - name: prod
    region: us-east-1
    replicas: 5

{% for env in environments %}
---
# {{ env.name }}-{{ env.region }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-{{ env.name }}
  namespace: {{ env.name }}
spec:
  replicas: {{ env.replicas }}
  template:
    spec:
      containers:
      - name: app
        image: myapp:{{ IMAGE_TAG | default('latest') }}
        env:
        - name: ENVIRONMENT
          value: {{ env.name }}
        - name: AWS_REGION
          value: {{ env.region }}
{% endfor %}
```

### Feature Flags and Conditional Configuration

```yaml
# feature-config.yml
{% set features = FEATURES | default('') | split(',') %}

app:
  name: {{ APP_NAME }}
  features:
{% for feature in features %}
    {{ feature }}: true
{% endfor %}

{% if 'auth' in features %}
authentication:
  provider: {{ AUTH_PROVIDER | default('local') }}
  jwt_secret: {{ JWT_SECRET }}
  {% if AUTH_PROVIDER == 'oauth' %}
  oauth:
    client_id: {{ OAUTH_CLIENT_ID }}
    client_secret: {{ OAUTH_CLIENT_SECRET }}
  {% endif %}
{% endif %}

{% if 'metrics' in features %}
monitoring:
  enabled: true
  endpoint: {{ METRICS_ENDPOINT | default('/metrics') }}
{% endif %}

{% if 'database' in features %}
database:
  {% if DATABASE_TYPE == 'postgres' %}
  postgres:
    url: {{ DATABASE_URL }}
    pool_size: {{ DB_POOL_SIZE | default(10) }}
  {% elif DATABASE_TYPE == 'mysql' %}
  mysql:
    url: {{ DATABASE_URL }}
    charset: utf8mb4
  {% endif %}
{% endif %}
```

Usage:

```bash
injinja \
  -e FEATURES=auth,metrics,database \
  -e AUTH_PROVIDER=oauth \
  -e DATABASE_TYPE=postgres \
  -e DATABASE_URL=postgres://localhost/myapp \
  -c feature-config.yml \
  -t app-config.j2
```

### Dynamic Service Discovery

Generate service configurations with automatic discovery:

```yaml
# services-config.yml
{% set service_count = REPLICAS | default(3) | int %}
{% set base_port = BASE_PORT | default(8000) | int %}

services:
{% for i in range(service_count) %}
  - name: {{ SERVICE_NAME }}-{{ i }}
    port: {{ base_port + i }}
    host: {{ SERVICE_NAME }}-{{ i }}.{{ DOMAIN | default('local') }}
    health_check: http://{{ SERVICE_NAME }}-{{ i }}:{{ base_port + i }}/health
    upstream_weight: {{ 100 // service_count }}
{% endfor %}

load_balancer:
  algorithm: {{ LB_ALGORITHM | default('round_robin') }}
  upstreams:
{% for i in range(service_count) %}
    - server {{ SERVICE_NAME }}-{{ i }}:{{ base_port + i }} weight={{ 100 // service_count }};
{% endfor %}
```

## Integration Examples

### Terraform Integration

Generate Terraform configurations:

```hcl
# terraform.tf.j2
terraform {
  required_version = ">= 1.0"

  backend "{{ TERRAFORM_BACKEND | default('local') }}" {
{% if TERRAFORM_BACKEND == 's3' %}
    bucket = "{{ S3_BUCKET }}"
    key    = "{{ S3_KEY }}"
    region = "{{ AWS_REGION }}"
{% elif TERRAFORM_BACKEND == 'consul' %}
    path = "{{ CONSUL_PATH }}"
    address = "{{ CONSUL_ADDRESS }}"
{% endif %}
  }
}

{% for env in environments %}
resource "aws_instance" "{{ env.name }}_web" {
  ami           = "{{ env.ami_id }}"
  instance_type = "{{ env.instance_type }}"
  count         = {{ env.instance_count }}

  tags = {
    Name        = "{{ APP_NAME }}-{{ env.name }}-web"
    Environment = "{{ env.name }}"
    Project     = "{{ PROJECT_NAME }}"
  }
}
{% endfor %}
```

### Docker Compose Integration

```yaml
# docker-compose.yml.j2
version: '3.8'

services:
  {% for service in services %}
  {{ service.name }}:
    image: {{ service.image }}:{{ IMAGE_TAG | default('latest') }}
    ports:
      - "{{ service.external_port }}:{{ service.internal_port }}"
    environment:
      {% for key, value in service.environment.items() %}
      - {{ key }}={{ value }}
      {% endfor %}
    {% if service.volumes %}
    volumes:
      {% for volume in service.volumes %}
      - {{ volume }}
      {% endfor %}
    {% endif %}
    {% if service.depends_on %}
    depends_on:
      {% for dep in service.depends_on %}
      - {{ dep }}
      {% endfor %}
    {% endif %}
  {% endfor %}

{% if networks %}
networks:
  {% for network in networks %}
  {{ network.name }}:
    driver: {{ network.driver | default('bridge') }}
  {% endfor %}
{% endif %}
```

### Kubernetes Integration

```yaml
# k8s-deployment.yml.j2
{% for app in applications %}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ app.name }}
  namespace: {{ NAMESPACE | default('default') }}
  labels:
    app: {{ app.name }}
    version: {{ IMAGE_TAG | default('latest') }}
spec:
  replicas: {{ app.replicas | default(1) }}
  selector:
    matchLabels:
      app: {{ app.name }}
  template:
    metadata:
      labels:
        app: {{ app.name }}
    spec:
      containers:
      - name: {{ app.name }}
        image: {{ app.image }}:{{ IMAGE_TAG | default('latest') }}
        ports:
        - containerPort: {{ app.port }}
        env:
        {% for env_var in app.environment %}
        - name: {{ env_var.name }}
          value: "{{ env_var.value }}"
        {% endfor %}
        resources:
          requests:
            memory: {{ app.resources.memory_request | default('256Mi') }}
            cpu: {{ app.resources.cpu_request | default('100m') }}
          limits:
            memory: {{ app.resources.memory_limit | default('512Mi') }}
            cpu: {{ app.resources.cpu_limit | default('500m') }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ app.name }}-service
  namespace: {{ NAMESPACE | default('default') }}
spec:
  selector:
    app: {{ app.name }}
  ports:
  - port: {{ app.service_port | default(80) }}
    targetPort: {{ app.port }}
  type: {{ app.service_type | default('ClusterIP') }}
{% endfor %}
```

## Performance Tips

### Large Configuration Sets

For large configuration sets:

1. **Use specific globs** instead of overly broad patterns
2. **Order config files** by merge priority (base first, overrides last)
3. **Break up large configs** into smaller, focused files

```bash
# Good: Specific and ordered
injinja -c 'config/base/*.yml' -c 'config/env/prod.yml' -c 'config/overrides/local.yml'

# Avoid: Too broad, unpredictable order
injinja -c 'config/**/*.yml'
```

### Template Optimization

1. **Minimize complex logic** in templates
2. **Use configuration preprocessing** for complex calculations
3. **Cache intermediate results** in configuration

```yaml
# Precompute complex values in config
computed:
  total_memory: {{ (WORKERS | default(4) | int) * (MEMORY_PER_WORKER | default(512) | int) }}
  connection_string: "{{ DB_TYPE }}://{{ DB_USER }}:{{ DB_PASS }}@{{ DB_HOST }}/{{ DB_NAME }}"

# Use in template
database:
  connection: {{ computed.connection_string }}

workers:
  count: {{ WORKERS | default(4) }}
  total_memory: {{ computed.total_memory }}MB
```

## Troubleshooting

### Common Issues

1. **Undefined Variable Errors**: Use defaults or conditional checks

```yaml
# Wrong
database_url: {{ DATABASE_URL }}

# Right
database_url: {{ DATABASE_URL | default('sqlite:///app.db') }}

# Or conditional
{% if DATABASE_URL %}
database_url: {{ DATABASE_URL }}
{% endif %}
```

1. **Merge Order Issues**: Explicitly control config file order

```bash
# Order matters - later configs override earlier ones
injinja -c base.yml -c environment.yml -c local-overrides.yml
```

1. **Template Syntax Issues**: Use debug mode to see parsed configuration

```bash
injinja --debug -c config.yml -t template.j2
```

### Debug Workflow

1. **Check environment variables**: `injinja --prefix MYAPP_ -o config-json`
2. **Validate configuration merge**: `injinja -c 'config/*.yml' -o config-yaml`
3. **Test template sections**: Create minimal test templates
4. **Use validation**: Compare against known-good output with `-v`

## Next Steps

- Learn about [Schema Validation](schema-validation.md) for validating configurations
- Check out the [API Reference](../api/injinja.md) for programmatic usage
- Explore the [Architecture](../architecture/overview.md) documentation
- See real-world examples in the project repository
