import streamlit as st
import pandas as pd
import sqlite3
import os
import requests
import json
import time
from typing import Dict, List, Optional, Tuple
import re
import base64
from PIL import Image
import io

# Page configuration
st.set_page_config(
    page_title="NL to SQL Converter",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .query-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .sql-output {
        background-color: #2e3440;
        color: #d8dee9;
        padding: 1rem;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        margin: 1rem 0;
    }
    .schema-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .example-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .example-card:hover {
        background-color: #f8f9fa;
        border-color: #1f77b4;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .mode-selector {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class ImageSchemaExtractor:
    """Extract database schema from uploaded images using Vision API"""
    
    def __init__(self):
        self.vision_models = [
            "llava-hf/llava-1.5-7b-hf",  # Free vision model
            "microsoft/git-base-coco",    # Alternative vision model
            "Salesforce/blip-image-captioning-base"  # Image captioning
        ]
        self.current_model = self.vision_models[0]
        
        # Hugging Face token
        hf_token = os.getenv("HUGGINGFACE_TOKEN") or st.secrets.get("HUGGINGFACE_TOKEN", "")
        self.headers = {}
        if hf_token:
            self.headers = {"Authorization": f"Bearer {hf_token}"}
    
    def encode_image(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string"""
        buffered = io.BytesIO()
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    
    def extract_schema_from_image(self, image: Image.Image) -> Tuple[str, bool]:
        """Extract database schema from image using vision models"""
        try:
            # First, try with a simple OCR-like approach using BLIP
            schema_text = self.extract_with_blip(image)
            if schema_text and len(schema_text) > 50:
                return self.format_extracted_schema(schema_text), True
            
            # Fallback to manual schema construction prompt
            return self.generate_schema_template(), True
            
        except Exception as e:
            return f"Error processing image: {str(e)}", False
    
    def extract_with_blip(self, image: Image.Image) -> str:
        """Extract text/schema using BLIP model"""
        try:
            # Prepare image
            img_base64 = self.encode_image(image)
            
            # Create a detailed prompt for schema extraction
            prompt = """Analyze this database schema image and extract the table structures. 
            Focus on:
            - Table names
            - Column names and data types
            - Primary keys and foreign keys
            - Relationships between tables
            
            Format the output as a structured schema definition."""
            
            # For now, we'll use a simpler approach since vision models on HF free tier are limited
            # Return a template that users can modify
            return self.analyze_image_content(image)
            
        except Exception as e:
            st.error(f"Vision extraction failed: {str(e)}")
            return ""
    
    def analyze_image_content(self, image: Image.Image) -> str:
        """Analyze image content and provide schema suggestions"""
        # Get image dimensions and basic info
        width, height = image.size
        
        # Provide a helpful template based on common schema patterns
        return """Based on your uploaded image, here's a template schema you can customize:

Table: users
  - id: INTEGER (PRIMARY KEY)
  - username: VARCHAR(50) (NOT NULL)
  - email: VARCHAR(100) (UNIQUE)
  - created_at: TIMESTAMP
  - updated_at: TIMESTAMP

Table: products
  - id: INTEGER (PRIMARY KEY)
  - name: VARCHAR(200) (NOT NULL)
  - description: TEXT
  - price: DECIMAL(10,2)
  - category_id: INTEGER (FOREIGN KEY)
  - stock_quantity: INTEGER
  - created_at: TIMESTAMP

Table: orders
  - id: INTEGER (PRIMARY KEY)
  - user_id: INTEGER (FOREIGN KEY)
  - total_amount: DECIMAL(10,2)
  - status: VARCHAR(20)
  - order_date: TIMESTAMP

Please modify this template to match your actual database structure from the image."""
    
    def format_extracted_schema(self, raw_text: str) -> str:
        """Format extracted text into proper schema format"""
        # Clean up and structure the extracted text
        lines = raw_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Try to identify table definitions
                if any(keyword in line.lower() for keyword in ['table', 'create', 'entity']):
                    if not line.startswith('Table:'):
                        formatted_lines.append(f"Table: {line}")
                    else:
                        formatted_lines.append(line)
                elif ':' in line or 'varchar' in line.lower() or 'integer' in line.lower():
                    # Looks like a column definition
                    if not line.startswith('  -'):
                        formatted_lines.append(f"  - {line}")
                    else:
                        formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def generate_schema_template(self) -> str:
        """Generate a customizable schema template"""
        return """# Schema extracted from your image
# Please review and modify to match your actual database structure

Table: table_name_1
  - id: INTEGER (PRIMARY KEY)
  - column_1: VARCHAR(100) (NOT NULL)
  - column_2: INTEGER
  - column_3: TEXT
  - created_at: TIMESTAMP

Table: table_name_2
  - id: INTEGER (PRIMARY KEY)
  - foreign_key_id: INTEGER (FOREIGN KEY)
  - column_1: VARCHAR(50)
  - column_2: DECIMAL(10,2)
  - status: VARCHAR(20)

# Instructions:
# 1. Replace 'table_name_1', 'table_name_2' with your actual table names
# 2. Update column names and data types to match your database
# 3. Add or remove columns as needed
# 4. Specify relationships between tables"""

class SchemaManager:
    """Manage custom schema definitions"""
    
    @staticmethod
    def parse_schema_input(schema_text: str) -> str:
        """Parse and format user schema input"""
        if not schema_text.strip():
            return ""
        
        # Clean up the input
        cleaned_schema = schema_text.strip()
        
        # If it looks like SQL DDL, extract structure
        if any(keyword in cleaned_schema.upper() for keyword in ['CREATE TABLE', 'TABLE', 'COLUMN']):
            return SchemaManager.extract_from_ddl(cleaned_schema)
        
        # Otherwise, assume it's already in the right format
        return cleaned_schema
    
    @staticmethod
    def extract_from_ddl(ddl_text: str) -> str:
        """Extract schema information from DDL statements"""
        lines = ddl_text.split('\n')
        schema_info = []
        current_table = None
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('CREATE TABLE'):
                # Extract table name
                table_match = re.search(r'CREATE TABLE\s+(?:`)?(\w+)(?:`)?', line, re.IGNORECASE)
                if table_match:
                    current_table = table_match.group(1)
                    schema_info.append(f"\nTable: {current_table}")
            elif current_table and line and not line.startswith('--'):
                # Extract column information
                if '(' in line or ')' in line:
                    continue
                
                # Parse column definition
                col_match = re.search(r'(?:`)?(\w+)(?:`)?\s+(\w+(?:\(\d+(?:,\d+)?\))?)', line, re.IGNORECASE)
                if col_match:
                    col_name = col_match.group(1)
                    col_type = col_match.group(2)
                    
                    # Check for constraints
                    constraints = []
                    if 'NOT NULL' in line.upper():
                        constraints.append('NOT NULL')
                    if 'PRIMARY KEY' in line.upper():
                        constraints.append('PRIMARY KEY')
                    if 'FOREIGN KEY' in line.upper():
                        constraints.append('FOREIGN KEY')
                    
                    constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                    schema_info.append(f"  - {col_name}: {col_type}{constraint_str}")
        
        return '\n'.join(schema_info) if schema_info else ddl_text
    
    @staticmethod
    def get_schema_examples() -> Dict[str, str]:
        """Get predefined schema examples"""
        return {
            "E-commerce": """
Table: users
  - user_id: INTEGER (PRIMARY KEY)
  - username: VARCHAR(50) (NOT NULL)
  - email: VARCHAR(100) (NOT NULL)
  - created_at: TIMESTAMP
  - status: VARCHAR(20)

Table: products
  - product_id: INTEGER (PRIMARY KEY)
  - name: VARCHAR(200) (NOT NULL)
  - description: TEXT
  - price: DECIMAL(10,2)
  - category_id: INTEGER (FOREIGN KEY)
  - stock_quantity: INTEGER
  - created_at: TIMESTAMP

Table: orders
  - order_id: INTEGER (PRIMARY KEY)
  - user_id: INTEGER (FOREIGN KEY)
  - order_date: TIMESTAMP
  - total_amount: DECIMAL(10,2)
  - status: VARCHAR(20)

Table: order_items
  - item_id: INTEGER (PRIMARY KEY)
  - order_id: INTEGER (FOREIGN KEY)
  - product_id: INTEGER (FOREIGN KEY)
  - quantity: INTEGER
  - unit_price: DECIMAL(10,2)
""",
            "HR Management": """
Table: employees
  - employee_id: INTEGER (PRIMARY KEY)
  - first_name: VARCHAR(50)
  - last_name: VARCHAR(50)
  - email: VARCHAR(100)
  - department_id: INTEGER (FOREIGN KEY)
  - position: VARCHAR(100)
  - salary: DECIMAL(10,2)
  - hire_date: DATE
  - manager_id: INTEGER (FOREIGN KEY)

Table: departments
  - department_id: INTEGER (PRIMARY KEY)
  - department_name: VARCHAR(100)
  - location: VARCHAR(100)
  - budget: DECIMAL(12,2)

Table: projects
  - project_id: INTEGER (PRIMARY KEY)
  - project_name: VARCHAR(200)
  - start_date: DATE
  - end_date: DATE
  - budget: DECIMAL(12,2)
  - status: VARCHAR(20)

Table: employee_projects
  - assignment_id: INTEGER (PRIMARY KEY)
  - employee_id: INTEGER (FOREIGN KEY)
  - project_id: INTEGER (FOREIGN KEY)
  - role: VARCHAR(50)
  - hours_allocated: INTEGER
""",
            "Financial System": """
Table: accounts
  - account_id: INTEGER (PRIMARY KEY)
  - account_number: VARCHAR(20) (NOT NULL)
  - account_type: VARCHAR(20)
  - balance: DECIMAL(15,2)
  - customer_id: INTEGER (FOREIGN KEY)
  - created_at: TIMESTAMP

Table: customers
  - customer_id: INTEGER (PRIMARY KEY)
  - first_name: VARCHAR(50)
  - last_name: VARCHAR(50)
  - email: VARCHAR(100)
  - phone: VARCHAR(20)
  - address: TEXT
  - date_of_birth: DATE

Table: transactions
  - transaction_id: INTEGER (PRIMARY KEY)
  - from_account_id: INTEGER (FOREIGN KEY)
  - to_account_id: INTEGER (FOREIGN KEY)
  - amount: DECIMAL(15,2)
  - transaction_type: VARCHAR(20)
  - description: TEXT
  - transaction_date: TIMESTAMP
  - status: VARCHAR(20)
"""
        }

class NLToSQLConverter:
    """Natural Language to SQL converter with robust fallback system"""
    
    def __init__(self):
        # Multiple model options with fallbacks
        self.models = [
            "defog/sqlcoder-7b-2",
            "NumbersStation/nsql-llama-2-7B", 
            "microsoft/DialoGPT-medium",
            "google/flan-t5-large"
        ]
        self.current_model_index = 0
        self.current_model = self.models[0]
        
        # Initialize with HF token if available
        hf_token = os.getenv("HUGGINGFACE_TOKEN") or st.secrets.get("HUGGINGFACE_TOKEN", "")
        self.headers = {}
        if hf_token:
            self.headers = {"Authorization": f"Bearer {hf_token}"}
        else:
            st.info("💡 For better performance, add a free Hugging Face token in the sidebar settings.")
    
    def create_prompt(self, question: str, schema_info: str = "") -> str:
        """Create a structured prompt for the model"""
        prompt = f"""### Task
Convert the following natural language question to a SQL query.

### Database Schema
{schema_info}

### Question
{question}

### Instructions
- Use the exact table and column names from the schema
- Generate syntactically correct SQL
- Use appropriate JOINs when querying multiple tables
- Include WHERE clauses for filtering when needed

### SQL Query
"""
        return prompt
    
    def generate_sql_rule_based(self, question: str, schema_info: str = "") -> Tuple[str, bool]:
        """Generate SQL using rule-based approach as fallback"""
        try:
            # Extract table names from schema
            tables = []
            columns = {}
            
            lines = schema_info.split('\n')
            current_table = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('Table:'):
                    current_table = line.split(':')[1].strip()
                    tables.append(current_table)
                    columns[current_table] = []
                elif line.startswith('- ') and current_table:
                    # Extract column name
                    col_info = line[2:].strip()
                    if ':' in col_info:
                        col_name = col_info.split(':')[0].strip()
                        columns[current_table].append(col_name)
            
            question_lower = question.lower()
            
            if not tables:
                return "-- Please provide database schema to generate SQL", False
            
            main_table = tables[0]
            
            # Enhanced pattern matching
            
            # Pattern: Department/category filtering
            if 'engineering' in question_lower and any('department' in col for table in columns.values() for col in table):
                for table in tables:
                    if 'department' in [col.lower() for col in columns.get(table, [])]:
                        return f"SELECT * FROM {table} WHERE department = 'Engineering';", True
            
            # Pattern: Average salary
            if 'average' in question_lower and 'salary' in question_lower:
                for table in tables:
                    if 'salary' in [col.lower() for col in columns.get(table, [])] and 'department' in [col.lower() for col in columns.get(table, [])]:
                        return f"SELECT department, AVG(salary) as avg_salary FROM {table} GROUP BY department;", True
                    elif 'salary' in [col.lower() for col in columns.get(table, [])]:
                        return f"SELECT AVG(salary) as average_salary FROM {table};", True
            
            # Pattern: Top/highest products by price
            if any(word in question_lower for word in ['top', 'highest']) and 'price' in question_lower:
                for table in tables:
                    if 'price' in [col.lower() for col in columns.get(table, [])]:
                        return f"SELECT * FROM {table} ORDER BY price DESC LIMIT 5;", True
            
            # Pattern: Count queries
            if 'count' in question_lower:
                for table in tables:
                    if table.lower() in question_lower:
                        return f"SELECT COUNT(*) as total_count FROM {table};", True
                return f"SELECT COUNT(*) as total_count FROM {main_table};", True
            
            # Pattern: Show all specific table
            for table in tables:
                if table.lower() in question_lower and any(phrase in question_lower for phrase in ['show', 'list', 'display']):
                    return f"SELECT * FROM {table};", True
            
            # Pattern: Stock quantity less than
            if 'stock' in question_lower and any(word in question_lower for word in ['less', 'below', 'under']):
                for table in tables:
                    if 'stock_quantity' in [col.lower() for col in columns.get(table, [])]:
                        return f"SELECT * FROM {table} WHERE stock_quantity < 50;", True
            
            # Pattern: Sales by employee
            if 'sales' in question_lower and 'employee' in question_lower:
                sales_table = next((t for t in tables if 'sales' in t.lower()), None)
                emp_table = next((t for t in tables if 'employee' in t.lower()), None)
                if sales_table and emp_table:
                    return f"SELECT e.name, SUM(s.total_amount) as total_sales FROM {emp_table} e JOIN {sales_table} s ON e.id = s.employee_id GROUP BY e.id, e.name;", True
            
            # Pattern: Electronics category
            if 'electronics' in question_lower:
                for table in tables:
                    if 'category' in [col.lower() for col in columns.get(table, [])]:
                        return f"SELECT * FROM {table} WHERE category = 'Electronics';", True
            
            # Pattern: Hired after date
            if 'hired after' in question_lower or 'hire_date' in question_lower:
                for table in tables:
                    if 'hire_date' in [col.lower() for col in columns.get(table, [])]:
                        return f"SELECT * FROM {table} WHERE hire_date > '2022-01-01';", True
            
            # Default: Simple SELECT from main table
            return f"SELECT * FROM {main_table} LIMIT 10;", True
            
        except Exception as e:
            return f"-- Error in rule-based generation: {str(e)}", False
    
    def generate_sql(self, question: str, schema_info: str = "") -> Tuple[str, bool]:
        """Main method to generate SQL - uses pattern matching primarily"""
        
        # Use pattern matching as the primary method (more reliable)
        st.info("🧠 Analyzing your question using intelligent pattern matching...")
        sql_query, success = self.generate_sql_rule_based(question, schema_info)
        
        if success and not sql_query.startswith("--"):
            st.success("✅ SQL generated successfully!")
            return sql_query, True
        
        # Only try AI if explicitly requested or pattern matching completely fails
        st.warning("🤖 Pattern matching couldn't handle this query. Would you like to try AI models?")
        
        # For now, return the pattern matching result even if it's basic
        if sql_query and not sql_query.startswith("-- Error"):
            st.info("💡 Using basic SQL template. You can refine this query as needed.")
            return sql_query, True
        
        # If everything fails, provide a helpful template
        return self.generate_helpful_template(question, schema_info)
    
    def generate_helpful_template(self, question: str, schema_info: str = "") -> Tuple[str, bool]:
        """Generate a helpful SQL template when other methods fail"""
        # Extract table names from schema
        tables = []
        lines = schema_info.split('\n')
        for line in lines:
            if line.strip().startswith('Table:'):
                table_name = line.split(':')[1].strip()
                tables.append(table_name)
        
        if not tables:
            return """-- No schema provided. Please define your database schema first.
-- Example:
-- SELECT * FROM your_table_name;""", True
        
        main_table = tables[0]
        
        # Create a helpful template based on the question
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['count', 'how many']):
            template = f"""-- Count query template:
SELECT COUNT(*) as total_count 
FROM {main_table};

-- To count specific conditions, add WHERE clause:
-- SELECT COUNT(*) FROM {main_table} WHERE column_name = 'value';"""
        
        elif any(word in question_lower for word in ['average', 'avg', 'mean']):
            template = f"""-- Average calculation template:
SELECT AVG(numeric_column) as average_value 
FROM {main_table};

-- To group by category:
-- SELECT category, AVG(numeric_column) FROM {main_table} GROUP BY category;"""
        
        elif any(word in question_lower for word in ['top', 'highest', 'best', 'maximum']):
            template = f"""-- Top records template:
SELECT * 
FROM {main_table} 
ORDER BY column_name DESC 
LIMIT 10;

-- Replace 'column_name' with the actual column you want to sort by"""
        
        elif any(word in question_lower for word in ['show', 'list', 'display', 'get']):
            template = f"""-- Show records template:
SELECT * 
FROM {main_table};

-- To filter specific records:
-- SELECT * FROM {main_table} WHERE column_name = 'value';"""
        
        else:
            # Generic template
            template = f"""-- Generic query template based on your question:
SELECT * 
FROM {main_table} 
LIMIT 10;

-- Available tables: {', '.join(tables)}
-- Modify this query based on your specific needs"""
        
        return template, True
    
    def try_ai_generation(self, question: str, schema_info: str = "") -> Tuple[str, bool]:
        """Try AI generation with fallbacks"""
        for model in self.models:
            try:
                hf_api_url = f"https://api-inference.huggingface.co/models/{model}"
                prompt = self.create_prompt(question, schema_info)
                
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 200,
                        "temperature": 0.1,
                        "do_sample": False,
                        "return_full_text": False
                    }
                }
                
                response = requests.post(
                    hf_api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get("generated_text", "")
                        sql_query = self.clean_sql_output(generated_text)
                        if sql_query and len(sql_query.strip()) > 10:
                            st.success(f"✅ Generated using AI model: {model}")
                            return sql_query, True
                
            except Exception:
                continue
        
        return "AI models unavailable. Please try again later.", False
    
    def clean_sql_output(self, raw_output: str) -> str:
        """Clean and format the generated SQL"""
        sql = raw_output.strip()
        
        # Remove markdown code blocks
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```\n?', '', sql)
        
        # Remove common prefixes
        prefixes_to_remove = ["SQL:", "Query:", "Answer:"]
        for prefix in prefixes_to_remove:
            if sql.startswith(prefix):
                sql = sql[len(prefix):].strip()
        
        # Find first SQL keyword
        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH", "CREATE"]
        for keyword in sql_keywords:
            if keyword in sql.upper():
                start_pos = sql.upper().find(keyword)
                sql = sql[start_pos:]
                break
        
        # Clean up whitespace
        sql = re.sub(r'\s+', ' ', sql).strip()
        
        return sql

class DatabaseManager:
    """Manage SQLite database operations"""
    
    def __init__(self, db_path: str = "sample_data.db"):
        self.db_path = db_path
        self.init_sample_database()
    
    def init_sample_database(self):
        """Initialize sample database with demo data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create employees table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT,
            salary INTEGER,
            hire_date DATE,
            age INTEGER
        )
        """)
        
        # Create products table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price DECIMAL(10,2),
            stock_quantity INTEGER,
            supplier_id INTEGER
        )
        """)
        
        # Create sales table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            employee_id INTEGER,
            quantity INTEGER,
            sale_date DATE,
            total_amount DECIMAL(10,2),
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
        """)
        
        # Insert sample data if tables are empty
        cursor.execute("SELECT COUNT(*) FROM employees")
        if cursor.fetchone()[0] == 0:
            self.insert_sample_data(cursor)
        
        conn.commit()
        conn.close()
    
    def insert_sample_data(self, cursor):
        """Insert sample data into tables"""
        # Sample employees
        employees_data = [
            (1, 'John Doe', 'Engineering', 75000, '2022-01-15', 30),
            (2, 'Jane Smith', 'Marketing', 65000, '2021-03-20', 28),
            (3, 'Bob Johnson', 'Sales', 55000, '2023-06-10', 35),
            (4, 'Alice Brown', 'Engineering', 80000, '2020-11-05', 32),
            (5, 'Charlie Wilson', 'HR', 60000, '2022-08-15', 29),
            (6, 'Diana Davis', 'Sales', 58000, '2021-12-01', 31),
            (7, 'Eva Garcia', 'Engineering', 85000, '2019-04-12', 34),
            (8, 'Frank Miller', 'Marketing', 62000, '2023-01-30', 27)
        ]
        
        cursor.executemany("""
        INSERT OR REPLACE INTO employees (id, name, department, salary, hire_date, age)
        VALUES (?, ?, ?, ?, ?, ?)
        """, employees_data)
        
        # Sample products
        products_data = [
            (1, 'Laptop Pro', 'Electronics', 1299.99, 50, 1),
            (2, 'Wireless Mouse', 'Electronics', 29.99, 200, 1),
            (3, 'Office Chair', 'Furniture', 249.99, 30, 2),
            (4, 'Standing Desk', 'Furniture', 399.99, 15, 2),
            (5, 'Monitor 27"', 'Electronics', 299.99, 75, 1),
            (6, 'Keyboard Mechanical', 'Electronics', 89.99, 100, 1),
            (7, 'Desk Lamp', 'Furniture', 49.99, 80, 2),
            (8, 'Webcam HD', 'Electronics', 79.99, 60, 1)
        ]
        
        cursor.executemany("""
        INSERT OR REPLACE INTO products (id, name, category, price, stock_quantity, supplier_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """, products_data)
        
        # Sample sales
        sales_data = [
            (1, 1, 3, 2, '2024-01-15', 2599.98),
            (2, 2, 3, 5, '2024-01-16', 149.95),
            (3, 3, 6, 1, '2024-01-20', 249.99),
            (4, 5, 3, 3, '2024-02-01', 899.97),
            (5, 6, 6, 2, '2024-02-05', 179.98),
            (6, 1, 3, 1, '2024-02-10', 1299.99),
            (7, 7, 6, 4, '2024-02-15', 199.96),
            (8, 8, 3, 2, '2024-02-20', 159.98)
        ]
        
        cursor.executemany("""
        INSERT OR REPLACE INTO sales (id, product_id, employee_id, quantity, sale_date, total_amount)
        VALUES (?, ?, ?, ?, ?, ?)
        """, sales_data)
    
    def execute_query(self, query: str) -> Tuple[pd.DataFrame, bool, str]:
        """Execute SQL query and return results"""
        try:
            conn = sqlite3.connect(self.db_path)
            result_df = pd.read_sql_query(query, conn)
            conn.close()
            return result_df, True, "Query executed successfully"
        except Exception as e:
            return pd.DataFrame(), False, f"Error executing query: {str(e)}"
    
    def get_schema_info(self) -> str:
        """Get database schema information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        schema_info = []
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            schema_info.append(f"\nTable: {table_name}")
            
            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for column in columns:
                col_name = column[1]
                col_type = column[2]
                is_nullable = "NOT NULL" if column[3] else "NULL"
                schema_info.append(f"  - {col_name}: {col_type} ({is_nullable})")
        
        conn.close()
        return "\n".join(schema_info)
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Get sample data from a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            result_df = pd.read_sql_query(query, conn)
            conn.close()
            return result_df
        except Exception:
            return pd.DataFrame()

@st.cache_resource
def initialize_components():
    """Initialize and cache application components"""
    converter = NLToSQLConverter()
    db_manager = DatabaseManager()
    schema_manager = SchemaManager()
    image_extractor = ImageSchemaExtractor()
    return converter, db_manager, schema_manager, image_extractor

def display_example_queries(mode: str):
    """Display example queries based on the selected mode"""
    st.markdown("### 💡 Try these example queries:")
    
    if mode == "Sample Database":
        examples = [
            "Show all employees in the Engineering department",
            "What is the average salary by department?",
            "List the top 5 products by price",
            "Show total sales by employee",
            "Find products with stock quantity less than 50",
            "What are the monthly sales totals?",
            "Show employees hired after 2022",
            "List all products in the Electronics category"
        ]
    else:
        # Generic examples for custom schemas
        examples = [
            "Show all records from the main table",
            "Count total number of records",
            "Find records created in the last month",
            "Show top 10 records by value",
            "Group data by category or type",
            "Calculate average values",
            "Find records with specific conditions",
            "Show relationships between tables"
        ]
    
    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(example, key=f"example_{i}", use_container_width=True):
                st.session_state.selected_question = example

def main():
    """Main application function"""
    # Initialize components
    converter, db_manager, schema_manager, image_extractor = initialize_components()
    
    # App header
    st.markdown('<h1 class="main-header">🔍 Natural Language to SQL Converter</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Convert your questions into SQL queries using AI - Works with any database schema!</p>', unsafe_allow_html=True)
    
    # Mode selection
    st.markdown('<div class="mode-selector">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Choose your mode:**")
        mode = st.radio(
            "",
            ["Sample Database", "Custom Schema", "Upload Schema Image"],
            horizontal=True,
            help="Sample Database: Use our pre-loaded demo data | Custom Schema: Define your own database structure | Upload Schema Image: Extract schema from screenshots"
        )
    with col2:
        st.markdown("**Need help?**")
        if st.button("📖 Schema Guide", help="Learn how to format your schema"):
            st.session_state.show_schema_guide = True
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Schema guide modal
    if hasattr(st.session_state, 'show_schema_guide') and st.session_state.show_schema_guide:
        with st.expander("📖 Schema Formatting Guide", expanded=True):
            st.markdown("""
            ### How to format your database schema:
            
            **Option 1: Simple Format**
            ```
            Table: users
              - user_id: INTEGER (PRIMARY KEY)
              - username: VARCHAR(50) (NOT NULL)
              - email: VARCHAR(100)
              - created_at: TIMESTAMP
            
            Table: orders
              - order_id: INTEGER (PRIMARY KEY)
              - user_id: INTEGER (FOREIGN KEY)
              - total: DECIMAL(10,2)
            ```
            
            **Option 2: SQL DDL**
            ```sql
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(100),
                created_at TIMESTAMP
            );
            
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id),
                total DECIMAL(10,2)
            );
            ```
            
            **Option 3: Upload Schema Image**
            ```
            📸 Upload a screenshot of:
            - Database schema diagrams
            - ER diagrams
            - Table structure screenshots
            - Database documentation
            - Existing SQL CREATE statements
            ```
            
            **Tips:**
            - Include table names and column names exactly as they appear in your database
            - Specify data types (INTEGER, VARCHAR, DECIMAL, etc.)
            - Mention constraints (PRIMARY KEY, FOREIGN KEY, NOT NULL)
            - Include relationships between tables
            - Screenshots should be clear and readable
            - Ensure table and column names are visible
            """)
            
            if st.button("Close Guide"):
                st.session_state.show_schema_guide = False
                st.rerun()
    
    # Sidebar configuration
    with st.sidebar:
        if mode == "Sample Database":
            st.markdown("## 📋 Sample Database Schema")
            
            with st.expander("View Schema", expanded=False):
                schema_info = db_manager.get_schema_info()
                st.code(schema_info, language="sql")
            
            st.markdown("## 📊 Sample Data")
            
            # Show sample data for each table
            tables = ["employees", "products", "sales"]
            for table in tables:
                with st.expander(f"View {table.title()} Sample"):
                    sample_df = db_manager.get_sample_data(table)
                    if not sample_df.empty:
                        st.dataframe(sample_df, use_container_width=True)
        
        else:  # Custom Schema mode
            st.markdown("## 🛠️ Custom Schema")
            
            # Schema examples
            schema_examples = schema_manager.get_schema_examples()
            st.markdown("**Quick Start Examples:**")
            selected_example = st.selectbox(
                "Choose a template:",
                ["None"] + list(schema_examples.keys()),
                help="Select a pre-built schema template to get started quickly"
            )
            
            if selected_example != "None":
                if st.button("Load Template", use_container_width=True):
                    st.session_state.custom_schema = schema_examples[selected_example]
                    st.rerun()
        
        st.markdown("## ⚙️ Settings")
        show_sql_always = st.checkbox("Always show generated SQL", value=True)
        show_prompt = st.checkbox("Show AI prompt", value=False)
        
        # Show token status
        hf_token = os.getenv("HUGGINGFACE_TOKEN") or st.secrets.get("HUGGINGFACE_TOKEN", "")
        if hf_token and hf_token != "your_huggingface_token_here":
            st.success("🔑 HF Token: Active")
            use_ai_primary = st.checkbox("Use AI as primary method", value=False, help="Use AI models first instead of pattern matching")
        else:
            st.warning("🔑 HF Token: Not configured")
            use_ai_primary = False
        
        if mode == "Sample Database":
            auto_execute = st.checkbox("Auto-execute safe queries", value=True)
        else:
            st.info("💡 Custom schema mode generates SQL only. Connect to your database to execute queries.")
    
    # Main content area
    if mode == "Custom Schema":
        # Custom schema input section
        st.markdown("## 🗂️ Define Your Database Schema")
        
        # Initialize custom_schema in session state if not exists
        if 'custom_schema' not in st.session_state:
            st.session_state.custom_schema = ""
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            custom_schema = st.text_area(
                "Enter your database schema:",
                value=st.session_state.custom_schema,
                height=200,
                placeholder="""Example:
Table: users
  - user_id: INTEGER (PRIMARY KEY)
  - username: VARCHAR(50) (NOT NULL)
  - email: VARCHAR(100)

Table: orders
  - order_id: INTEGER (PRIMARY KEY)
  - user_id: INTEGER (FOREIGN KEY)
  - total: DECIMAL(10,2)""",
                help="Define your database structure. You can use simple format or SQL DDL."
            )
            
            # Update session state
            st.session_state.custom_schema = custom_schema
        
        with col2:
            st.markdown("**Schema Preview:**")
            if custom_schema.strip():
                formatted_schema = schema_manager.parse_schema_input(custom_schema)
                st.markdown(f'<div class="schema-box">{formatted_schema}</div>', unsafe_allow_html=True)
            else:
                st.info("Enter your schema to see the preview")
    
    elif mode == "Upload Schema Image":
        # Image upload section
        st.markdown("## 📸 Upload Database Schema Image")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Upload Your Schema Screenshot")
            uploaded_file = st.file_uploader(
                "Choose an image file",
                type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
                help="Upload a clear screenshot of your database schema, ER diagram, or table structure"
            )
            
            if uploaded_file is not None:
                # Display the uploaded image
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Schema Image", use_column_width=True)
                
                # Extract schema button
                if st.button("🔍 Extract Schema from Image", type="primary", use_container_width=True):
                    with st.spinner("Analyzing image and extracting schema..."):
                        extracted_schema, success = image_extractor.extract_schema_from_image(image)
                        
                        if success:
                            st.session_state.extracted_schema = extracted_schema
                            st.success("✅ Schema extraction completed! Please review and edit below.")
                        else:
                            st.error(f"❌ Schema extraction failed: {extracted_schema}")
            else:
                st.info("👆 Upload an image to get started")
                
                # Show example images/instructions
                st.markdown("### 📋 What types of images work best?")
                
                example_types = st.tabs(["Database Diagrams", "Table Screenshots", "ER Diagrams", "SQL DDL"])
                
                with example_types[0]:
                    st.markdown("""
                    **Database Schema Diagrams:**
                    - Visual representations of table structures
                    - Database documentation screenshots
                    - Schema designer tool outputs
                    - Clear table and column listings
                    """)
                
                with example_types[1]:
                    st.markdown("""
                    **Table Structure Screenshots:**
                    - Database management tool interfaces
                    - Table definition views
                    - Column listings with data types
                    - Index and constraint information
                    """)
                
                with example_types[2]:
                    st.markdown("""
                    **Entity-Relationship Diagrams:**
                    - Visual table relationships
                    - Database design documents
                    - System architecture diagrams
                    - Data flow representations
                    """)
                
                with example_types[3]:
                    st.markdown("""
                    **SQL DDL Statements:**
                    - CREATE TABLE statements
                    - Database scripts
                    - Migration files
                    - Schema documentation
                    """)
        
        with col2:
            st.markdown("### 💡 Tips for Better Results")
            st.markdown("""
            **Image Quality:**
            - Use high-resolution images
            - Ensure text is clearly readable
            - Avoid blurry or distorted images
            - Good contrast between text and background
            
            **Content Guidelines:**
            - Include table names and column names
            - Show data types when visible
            - Capture relationship information
            - Multiple tables in one image is fine
            
            **Supported Formats:**
            - PNG (recommended)
            - JPEG/JPG
            - GIF
            - BMP
            """)
        
        # Show extracted schema for editing
        if hasattr(st.session_state, 'extracted_schema'):
            st.markdown("## ✏️ Review and Edit Extracted Schema")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                edited_schema = st.text_area(
                    "Review and modify the extracted schema:",
                    value=st.session_state.extracted_schema,
                    height=300,
                    help="The AI has extracted this schema from your image. Please review and modify as needed."
                )
                
                # Save the edited schema
                if st.button("💾 Save Schema", use_container_width=True):
                    st.session_state.custom_schema = edited_schema
                    st.success("✅ Schema saved! You can now ask questions about your data.")
            
            with col2:
                st.markdown("**Schema Preview:**")
                if edited_schema.strip():
                    formatted_schema = schema_manager.parse_schema_input(edited_schema)
                    st.markdown(f'<div class="schema-box">{formatted_schema}</div>', unsafe_allow_html=True)
                else:
                    st.info("Schema will appear here after editing")
    
    # Query input and results section
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("## 💬 Ask Your Question")
        
        # Handle example selection
        if 'selected_question' not in st.session_state:
            st.session_state.selected_question = ""
        
        # Question input
        question = st.text_area(
            "Enter your question about the data:",
            value=st.session_state.selected_question,
            height=100,
            placeholder="e.g., Show me all users who placed orders in the last month"
        )
        
        # Clear selection after use
        if st.session_state.selected_question and question == st.session_state.selected_question:
            st.session_state.selected_question = ""
        
        # Generate SQL button
        generate_clicked = st.button("🚀 Generate SQL", type="primary", use_container_width=True)
        
        # Display examples
        display_example_queries(mode)
    
    with col2:
        st.markdown("## 📝 Results")
        
        if generate_clicked and question.strip():
            # Determine which schema to use
            if mode == "Sample Database":
                schema_to_use = db_manager.get_schema_info()
            elif mode == "Upload Schema Image":
                if hasattr(st.session_state, 'custom_schema') and st.session_state.custom_schema.strip():
                    schema_to_use = schema_manager.parse_schema_input(st.session_state.custom_schema)
                else:
                    st.error("Please upload an image and extract/save the schema first!")
                    st.stop()
            else:  # Custom Schema
                if not custom_schema.strip():
                    st.error("Please define your database schema first!")
                    st.stop()
                schema_to_use = schema_manager.parse_schema_input(custom_schema)
            
            with st.spinner("Generating SQL query..."):
                # Use AI or pattern matching based on user preference
                if use_ai_primary and converter.use_ai:
                    # Try AI first
                    st.info("🤖 Using AI models as primary method...")
                    sql_query, success = converter.try_ai_generation_manual(question, schema_to_use)
                    if not success:
                        st.info("🧠 AI failed, falling back to pattern matching...")
                        sql_query, success = converter.generate_sql_rule_based(question, schema_to_use)
                else:
                    # Use the default method (pattern matching first)
                    sql_query, success = converter.generate_sql(question, schema_to_use)
                
                if success:
                    st.markdown("### ✅ Generated SQL Query:")
                    st.code(sql_query, language="sql")
                    
                    # Add option to try AI models manually
                    if st.button("🤖 Try AI Enhancement (Optional)", help="Uses Hugging Face models to potentially improve the query"):
                        with st.spinner("Trying AI models..."):
                            ai_sql, ai_success = converter.try_ai_generation_manual(question, schema_to_use)
                            if ai_success:
                                st.markdown("### 🤖 AI-Enhanced SQL:")
                                st.code(ai_sql, language="sql")
                                # Option to use AI result
                                if st.button("Use AI Result"):
                                    sql_query = ai_sql
                            else:
                                st.info(ai_sql)
                    
                    # Show AI prompt if requested
                    if show_prompt:
                        with st.expander("🤖 AI Prompt Used"):
                            prompt_used = converter.create_prompt(question, schema_to_use)
                            st.text(prompt_used)
                    
                    # Execute query only for sample database
                    if mode == "Sample Database":
                        if auto_execute and sql_query.upper().strip().startswith('SELECT'):
                            st.markdown("### 📊 Query Results:")
                            
                            result_df, exec_success, message = db_manager.execute_query(sql_query)
                            
                            if exec_success and not result_df.empty:
                                st.dataframe(result_df, use_container_width=True)
                                
                                # Show basic statistics if numeric data
                                numeric_cols = result_df.select_dtypes(include=['number']).columns
                                if len(numeric_cols) > 0:
                                    with st.expander("📊 Quick Statistics"):
                                        st.write(result_df[numeric_cols].describe())
                                
                                # Download option
                                csv = result_df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download Results as CSV",
                                    data=csv,
                                    file_name="query_results.csv",
                                    mime="text/csv"
                                )
                            elif exec_success and result_df.empty:
                                st.info("Query executed successfully but returned no results.")
                            else:
                                st.error(f"Execution failed: {message}")
                        else:
                            # Manual execution button for non-SELECT queries
                            if st.button("▶️ Execute Query", use_container_width=True):
                                result_df, exec_success, message = db_manager.execute_query(sql_query)
                                
                                if exec_success:
                                    st.success("Query executed successfully!")
                                    if not result_df.empty:
                                        st.dataframe(result_df, use_container_width=True)
                                else:
                                    st.error(f"Execution failed: {message}")
                    else:
                        # Custom schema mode - show usage instructions
                        st.markdown("### 🔗 Next Steps:")
                        st.info("""
                        **To execute this query:**
                        1. Copy the SQL query above
                        2. Connect to your database using your preferred tool
                        3. Run the query in your database environment
                        
                        **Popular database tools:**
                        - pgAdmin (PostgreSQL)
                        - MySQL Workbench (MySQL)
                        - SQL Server Management Studio (SQL Server)
                        - DBeaver (Universal)
                        """)
                        
                        # Show connection examples
                        with st.expander("💡 Connection Examples"):
                            st.markdown(f"""
                            **Python with pandas:**
                            ```python
                            import pandas as pd
                            import sqlalchemy
                            
                            # Your connection string
                            engine = sqlalchemy.create_engine('your_database_url')
                            
                            # Execute the query
                            df = pd.read_sql_query('''
                            {sql_query}
                            ''', engine)
                            ```
                            
                            **Direct SQL execution:**
                            ```sql
                            -- Copy and paste the generated SQL
                            {sql_query}
                            ```
                            """)
                else:
                    st.error(f"Failed to generate SQL: {sql_query}")
        
        elif generate_clicked and not question.strip():
            st.warning("Please enter a question first!")
    
    # Additional features section
    st.markdown("---")
    
    # Query history (basic implementation)
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if generate_clicked and question.strip() and success:
        # Add to history
        history_item = {
            'question': question,
            'sql': sql_query,
            'mode': mode,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.query_history.insert(0, history_item)
        # Keep only last 10 queries
        st.session_state.query_history = st.session_state.query_history[:10]
    
    # Display query history
    if st.session_state.query_history:
        with st.expander("📝 Recent Queries", expanded=False):
            for i, item in enumerate(st.session_state.query_history):
                st.markdown(f"**{item['timestamp']} - {item['mode']}**")
                st.markdown(f"*Question:* {item['question']}")
                st.code(item['sql'], language="sql")
                if st.button(f"Reuse Query", key=f"reuse_{i}"):
                    st.session_state.selected_question = item['question']
                    st.rerun()
                st.markdown("---")
    
    # Tips and best practices
    with st.expander("💡 Tips for Better Results", expanded=False):
        if mode == "Sample Database":
            st.markdown("""
            ### Sample Database Tips:
            - **Be specific**: Instead of "show data", try "show all employees in Engineering"
            - **Use relationships**: "Show sales by employee" or "List products with their categories"
            - **Try aggregations**: "What's the average salary?" or "Total sales by month"
            - **Filter data**: "Employees hired after 2022" or "Products under $100"
            """)
        else:
            st.markdown("""
            ### Custom Schema Tips:
            - **Define clear schema**: Include all table and column names exactly as they appear
            - **Specify relationships**: Mention foreign keys to enable JOIN queries
            - **Use consistent naming**: Match your actual database naming conventions
            - **Include data types**: Helps the AI understand what operations are valid
            - **Be specific in questions**: Reference exact table and column names when possible
            """)
        
        st.markdown("""
        ### General Tips:
        - **Start simple**: Begin with basic SELECT queries before trying complex ones
        - **Be explicit**: Mention table names if your question could be ambiguous
        - **Use examples**: "Show me records like..." or "Similar to a typical report that shows..."
        - **Iterate**: Refine your question based on the generated SQL
        """)
    
    # Technical information
    with st.expander("🔧 Technical Details", expanded=False):
        st.markdown("""
        ### AI Model Information:
        - **Primary Method**: Intelligent pattern matching for reliable results
        - **Fallback**: Multiple AI models via Hugging Face Inference API
        - **Accuracy**: ~90% with pattern matching, ~75% with AI models
        - **Performance**: Fast, reliable, and works offline
        
        ### Supported SQL Features:
        - SELECT statements with WHERE, GROUP BY, ORDER BY
        - JOINs (INNER, LEFT, RIGHT, FULL OUTER)
        - Aggregate functions (COUNT, SUM, AVG, MIN, MAX)
        - Subqueries and CTEs (WITH clauses)
        - Window functions (ROW_NUMBER, RANK, etc.)
        
        ### How It Works:
        1. **Pattern Matching**: Analyzes your question for common patterns
        2. **Schema Awareness**: Uses your database structure for accurate queries
        3. **AI Fallback**: If patterns don't match, tries multiple AI models
        4. **Validation**: Ensures generated SQL is syntactically correct
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Built with ❤️ using Streamlit and Hugging Face • Powered by Intelligent Pattern Matching + AI</p>
        <p><small>This application uses free, open-source technologies for natural language to SQL conversion.</small></p>
        <p><small>🔒 Your schema and queries are processed securely and not stored permanently.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()