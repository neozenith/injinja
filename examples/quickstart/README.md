# Quickstart

## **Step 1**: Config files with the power of `Jinja`

`config/databases.yml`

```yml
databases:
  {{ prefix | default('') | upper }}{{env_name | upper}}_BRONZE:
    description: Raw ingestion layer of our medallion architecture. Read only access for dbt. Write only for ingestion tools.

  {{ prefix | default('') | upper }}{{env_name | upper}}_SILVER:
    description: Primary data modelling area manmaged by dbt.

  {{ prefix | default('') | upper }}{{env_name | upper}}_GOLD:
    description: Curated and well modelled data. Read only access to BI tools.
```

### **Step 2**: Templating foundational files with your conventions

`sql/databases.sql.j2`

```sql
-- Create Databases
{% for database_name, database_properties in databases.items() -%}
CREATE OR ALTER DATABASE {{ database_name }}
    {%- if database_properties.description is defined %}
    WITH COMMENT = '{{ database_properties.description }}'
    {%- endif -%}
    ;
{% endfor %}
```

### **Step 3**: One config for every environment (and branch)

**3a** _Generate PROD SQL statements_

```sh
# Template SQL DDL with dynamic environment variables and static config
uvx injinja \
-e env_name=prod \
-c 'config/*' \
-t sql/databases.sql.j2
```

```sql
-- Create Databases
CREATE OR ALTER DATABASE PROD_BRONZE
    WITH COMMENT = 'Raw ingestion layer of our medallion architecture. Read only access for dbt. Write only for ingestion tools.';
CREATE OR ALTER DATABASE PROD_SILVER
    WITH COMMENT = 'Primary data modelling area manmaged by dbt.';
CREATE OR ALTER DATABASE PROD_GOLD
    WITH COMMENT = 'Curated and well modelled data. Read only access to BI tools.';
```

**3b** _Generate DEV Databases per branch_

```sh
# Inject normalised git branch prefix
uvx injinja \
-e env_name=dev \
-e prefix="$(git symbolic-ref --short HEAD | sed 's/\//_/g')__" \ 
-c 'config/*' \
-t sql/databases.sql.j2
```

Assuming our git branch was `JIRA-123/incremental-model`:

```sql
-- Create Databases
CREATE OR ALTER DATABASE JIRA-123_INCREMENTAL-MODEL__DEV_BRONZE
    WITH COMMENT = 'Raw ingestion layer of our medallion architecture. Read only access for dbt. Write only for ingestion tools.';
CREATE OR ALTER DATABASE JIRA-123_INCREMENTAL-MODEL__DEV_SILVER
    WITH COMMENT = 'Primary data modelling area manmaged by dbt.';
CREATE OR ALTER DATABASE JIRA-123_INCREMENTAL-MODEL__DEV_GOLD
    WITH COMMENT = 'Curated and well modelled data. Read only access to BI tools.';
```
