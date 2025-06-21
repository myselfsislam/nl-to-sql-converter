# 🔍 Natural Language to SQL Converter

A powerful Streamlit application that converts natural language questions into SQL queries using free, open-source AI models. Now with **image upload functionality** to extract database schemas from screenshots!

## 🚀 Features

- **🤖 AI-Powered Conversion**: Uses Hugging Face's DuckDB-NSQL-7B model
- **📸 Image Schema Extraction**: Upload screenshots to automatically generate database schemas
- **🎯 Three Operation Modes**: Sample database, custom schema input, or image upload
- **💻 Interactive Interface**: Clean, user-friendly Streamlit interface
- **📊 Real-time Execution**: Execute generated SQL queries instantly (sample mode)
- **🗂️ Schema Visualization**: View database structure and sample data
- **📥 Export Results**: Download query results as CSV
- **💡 Smart Examples**: Click-to-try example questions
- **📝 Query History**: Track and reuse recent queries

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **AI Model**: DuckDB-NSQL-7B via Hugging Face Inference API
- **Image Processing**: PIL (Python Imaging Library)
- **Database**: SQLite (for demo data)
- **Backend**: Python with pandas, requests
- **Deployment**: Streamlit Community Cloud / Vercel compatible

## 📦 Quick Start

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd nl-to-sql-converter
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 🌐 Deployment Options

### Option 1: Streamlit Community Cloud (Recommended)

1. **Push code to GitHub**
2. **Visit [share.streamlit.io](https://share.streamlit.io/)**
3. **Connect your GitHub repository**
4. **Deploy automatically**

### Option 2: Vercel

1. **Install Vercel CLI**
```bash
npm i -g vercel
```

2. **Deploy**
```bash
vercel --prod
```

### Option 3: Hugging Face Spaces

1. **Create new Space** at [huggingface.co/spaces](https://huggingface.co/spaces)
2. **Select Streamlit SDK**
3. **Upload your files**

## 📋 File Structure

```
nl-to-sql-converter/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── runtime.txt              # Python version specification
├── vercel.json              # Vercel deployment config
├── .streamlit/
│   ├── config.toml          # Streamlit configuration
│   └── secrets.toml         # Secrets (create from template)
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## 🔧 Configuration

### Environment Variables (Optional)

For better performance and higher rate limits, set up a free Hugging Face token:

1. **Create account** at [Hugging Face](https://huggingface.co/)
2. **Generate token** in Settings > Access Tokens
3. **Add to environment**:

**Local Development:**
```bash
export HUGGINGFACE_TOKEN="your_token_here"
```

**Streamlit Cloud:**
- Add in the Streamlit dashboard secrets section

**Vercel:**
- Add in Vercel dashboard environment variables

Or create `.streamlit/secrets.toml`:
```toml
HUGGINGFACE_TOKEN = "your_token_here"
```

## 🎯 How to Use

### 1. **Sample Database Mode**
- Use pre-loaded demo data with employees, products, and sales
- Perfect for testing and learning
- Includes real-time query execution

### 2. **Custom Schema Mode**
- Define your own database structure manually
- Supports simple format or SQL DDL
- Choose from pre-built templates (E-commerce, HR, Financial)

### 3. **Upload Schema Image** 🆕
- Upload screenshots of database schemas
- Supports ER diagrams, table structures, SQL DDL
- AI extracts schema automatically
- Review and edit before use

## 📸 Image Upload Guide

### Supported Image Types:
- **Database schema diagrams**
- **ER diagrams from design tools**
- **Table structure screenshots**
- **SQL DDL statements**
- **Database documentation**

### Best Practices:
- Use high-resolution, clear images
- Ensure text is readable
- Include table and column names
- Show data types and relationships
- Supported formats: PNG, JPEG, GIF, BMP

## 💡 Example Queries

### Sample Database:
- "Show all employees in the Engineering department"
- "What is the average salary by department?"
- "List the top 5 products by price"
- "Show total sales by employee"

### Custom Schema:
- "Show all users who placed orders last month"
- "Calculate total revenue by product category"
- "Find customers with more than 5 orders"
- "List top performing sales representatives"

## 🔧 Technical Details

### AI Model Information:
- **Model**: DuckDB-NSQL-7B (Specialized for SQL generation)
- **Provider**: Hugging Face Inference API (Free tier)
- **Accuracy**: ~75% on standard benchmarks
- **Specialization**: Optimized for DuckDB but works with standard SQL

### Supported SQL Features:
- SELECT statements with WHERE, GROUP BY, ORDER BY
- JOINs (INNER, LEFT, RIGHT, FULL OUTER)
- Aggregate functions (COUNT, SUM, AVG, MIN, MAX)
- Subqueries and CTEs (WITH clauses)
- Window functions (ROW_NUMBER, RANK, etc.)

### Limitations:
- Complex stored procedures may not be supported
- Database-specific functions might need manual adjustment
- Always review generated SQL before execution
- Large schemas might exceed context limits

## 🚨 Important Notes

### Free Tier Limitations:
- Hugging Face API has rate limits (generous for demos)
- Cold start delays of 10-20 seconds when model loads
- No persistent storage on free deployments

### Security Features:
- Input validation prevents basic SQL injection
- Only SELECT queries auto-execute in sample mode
- Schema information helps validate table/column names
- No data is stored permanently

## 🐛 Troubleshooting

### Common Issues:

**"Model is loading"**
- Wait 10-20 seconds and retry
- This is normal for free API cold starts

**API Rate Limits**
- Add Hugging Face token for higher limits
- Consider spacing out requests

**Deployment Errors**
- Check requirements.txt compatibility
- Verify Python version in runtime.txt
- Ensure all files are present

**Image Upload Issues**
- Verify image format is supported
- Check image size and quality
- Ensure text is clearly readable

## 📝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is open-source and free to use. Built with:

- [Streamlit](https://streamlit.io/) - Apache 2.0 License
- [DuckDB-NSQL-7B](https://huggingface.co/motherduckdb/DuckDB-NSQL-7B-v0.1) - Apache 2.0 License
- [Hugging Face](https://huggingface.co/) - Free Inference API

## 🤝 Support

- **Issues**: Create GitHub issues for bugs
- **Questions**: Use GitHub discussions
- **Documentation**: Check this README and code comments

## 🎉 Acknowledgments

- Hugging Face for providing free AI model inference
- Streamlit for the amazing web framework
- Numbers Station for the DuckDB-NSQL model
- The open-source community for inspiration and tools

---

**Built with ❤️ using free, open-source technologies**

Made possible by the amazing open-source AI and web development communities!
