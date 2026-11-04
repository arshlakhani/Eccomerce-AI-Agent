import os
import pandas as pd

from sqlalchemy import text
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from dotenv import load_dotenv
from pathlib import Path
from database import engine

# Load environment variables from this backend folder.
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)



# 1. ANALYTICS TOOLS

@tool
def anomaly_detection_tool(threshold: int = 100, limit: int = 10) -> str:
    """Find unusually high-quantity transactions.
    Use for questions about suspicious transactions or sales anomalies.
    Threshold sets the minimum quantity to flag.
    Limit sets the maximum number of transactions to return.
    """
    query = text("""
                SELECT
                    "InvoiceNo",
                    "Description",
                    "Quantity",
                    "Revenue",
                    CASE
                        WHEN "Quantity" > :high_threshold THEN 'High Risk'
                        WHEN "Quantity" > :threshold THEN 'Review'
                        ELSE 'Normal'
                    END AS anomaly_status
                FROM online_retail
                WHERE "Quantity" > :threshold
                ORDER BY "Quantity" DESC
                LIMIT :limit;
            """)

    with engine.connect() as connection:
        results = pd.read_sql(
            query,
            connection,
            params={
                "threshold": threshold,
                "high_threshold": threshold * 10,
                "limit": limit
            }
        )
    return results.to_json(orient="records")


@tool
def monthly_revenue_tool() -> str:
    """Analyze monthly revenue and month-over-month growth.
    Use for questions about monthly sales, revenue trends, increases or declines.
    """
    query = text("""
                WITH monthly_sales AS (
                    SELECT
                        "Month",
                        SUM("Revenue") AS monthly_revenue
                    FROM online_retail
                    GROUP BY "Month"
                ),
                monthly_comparison AS (
                    SELECT
                        "Month",
                        monthly_revenue,
                        LAG(monthly_revenue) OVER (ORDER BY "Month") AS previous_revenue
                    FROM monthly_sales
                )
                SELECT
                    "Month",
                    ROUND(monthly_revenue::numeric, 2) AS revenue,
                    ROUND(previous_revenue::numeric, 2) AS previous_revenue,
                    ROUND(
                        (
                            (monthly_revenue - previous_revenue)
                            / NULLIF(previous_revenue, 0) * 100
                        )::numeric,
                        2
                    ) AS growth_percentage
                FROM monthly_comparison
                ORDER BY "Month";
            """)

    with engine.connect() as connection:
        results = pd.read_sql(query, connection)
    return results.to_json(orient="records")


@tool
def top_products_tool(limit: int = 10) -> str:
    """Find products ranked by total revenue.
    Use for questions about top products, product performance or highest product revenue.
    """
    query = text("""
                SELECT
                    "StockCode",
                    "Description",
                    SUM("Quantity") AS total_units_sold,
                    ROUND(SUM("Revenue")::numeric, 2) AS total_revenue,
                    COUNT(DISTINCT "InvoiceNo") AS total_invoices
                FROM online_retail
                WHERE "Quantity" > 0
                  AND "Revenue" > 0
                  AND "Description" IS NOT NULL
                GROUP BY "StockCode", "Description"
                ORDER BY total_revenue DESC
                LIMIT :limit;
            """)

    with engine.connect() as connection:
        results = pd.read_sql(query, connection, params={"limit": limit})
    return results.to_json(orient="records")


@tool
def customer_analytics_tool(limit: int = 10) -> str:
    """Analyze customer purchasing behaviour.
    Returns customers ranked by total revenue, including invoice count and quantity.
    Use for questions about top customers or customer spending.
    """
    query = text("""
                SELECT
                    "CustomerID",
                    COUNT(DISTINCT "InvoiceNo") AS total_invoices,
                    SUM("Quantity") AS total_quantity,
                    SUM("Revenue") AS total_revenue
                FROM online_retail
                WHERE "CustomerID" IS NOT NULL
                  AND "Quantity" > 0
                  AND "Revenue" > 0
                GROUP BY "CustomerID"
                ORDER BY total_revenue DESC
                LIMIT :limit;
            """)

    with engine.connect() as connection:
        results = pd.read_sql(query, connection, params={"limit": limit})
    return results.to_json(orient="records")


@tool
def country_sales_tool(limit: int = 10) -> str:
    """Analyze sales performance by country.
    Use for questions about country-wise revenue, invoices, sales rankings or geography.
    """
    query = text("""
                SELECT
                    "Country",
                    COUNT(DISTINCT "InvoiceNo") AS total_invoices,
                    COUNT(DISTINCT "CustomerID") AS unique_customers,
                    SUM("Quantity") AS total_quantity,
                    SUM("Revenue") AS total_revenue
                FROM online_retail
                WHERE "Quantity" > 0
                  AND "Revenue" > 0
                GROUP BY "Country"
                ORDER BY total_revenue DESC
                LIMIT :limit;
            """)

    with engine.connect() as connection:
        results = pd.read_sql(query, connection, params={"limit": limit})
    return results.to_json(orient="records")


@tool
def business_summary_tool() -> str:
    """Provide an overall business summary.
    Use for questions about total revenue, invoices, customers, units sold and countries.
    """
    query = text("""
                SELECT
                    SUM("Revenue") AS total_revenue,
                    SUM("Quantity") AS total_quantity,
                    COUNT(DISTINCT "InvoiceNo") AS total_invoices,
                    COUNT(DISTINCT "CustomerID") AS unique_customers,
                    COUNT(DISTINCT "Country") AS total_countries
                FROM online_retail
                WHERE "Quantity" > 0
                  AND "Revenue" > 0;
            """)

    with engine.connect() as connection:
        results = pd.read_sql(query, connection)
    return results.to_json(orient="records")


@tool
def repeat_customer_tool() -> str:
    """Analyze repeat purchasing behaviour.
    Use for questions about repeat customers, customer retention and purchase frequency.
    """
    query = text("""
                WITH customer_orders AS (
                    SELECT
                        "CustomerID",
                        COUNT(DISTINCT "InvoiceNo") AS invoice_count,
                        SUM("Revenue") AS total_spending
                    FROM online_retail
                    WHERE "CustomerID" IS NOT NULL
                      AND "Quantity" > 0
                      AND "Revenue" > 0
                    GROUP BY "CustomerID"
                )
                SELECT
                    COUNT(*) AS total_customers,
                    COUNT(*) FILTER (WHERE invoice_count > 1) AS repeat_customers,
                    ROUND(
                        100.0 * COUNT(*) FILTER (WHERE invoice_count > 1)
                        / NULLIF(COUNT(*), 0), 2
                    ) AS repeat_customer_percentage,
                    ROUND(AVG(invoice_count), 2) AS avg_invoices_per_customer
                FROM customer_orders;
            """)

    with engine.connect() as connection:
        results = pd.read_sql(query, connection)
    return results.to_json(orient="records")


@tool
def monthly_product_analysis_tool(
        year: int, month: int, limit: int = 10
) -> str:
    """Find the highest-revenue products in a particular month and year."""
    query = text("""
                SELECT
                    "StockCode",
                    "Description",
                    SUM("Quantity") AS total_quantity,
                    SUM("Revenue") AS total_revenue,
                    COUNT(DISTINCT "InvoiceNo") AS total_invoices
                FROM online_retail
                WHERE EXTRACT(YEAR FROM "InvoiceDate") = :year
                  AND EXTRACT(MONTH FROM "InvoiceDate") = :month
                  AND "Quantity" > 0
                  AND "Revenue" > 0
                GROUP BY "StockCode", "Description"
                ORDER BY total_revenue DESC
                LIMIT :limit;
            """)

    with engine.connect() as connection:
        results = pd.read_sql(
            query,
            connection,
            params={"year": year, "month": month, "limit": limit}
        )
    return results.to_json(orient="records")


@tool
def monthly_country_analysis_tool(
        year: int, month: int, limit: int = 10
) -> str:
    """Analyze revenue, invoices and customers by country for a specific month."""
    query = text("""
                SELECT
                    "Country",
                    SUM("Revenue") AS total_revenue,
                    SUM("Quantity") AS total_quantity,
                    COUNT(DISTINCT "InvoiceNo") AS total_invoices,
                    COUNT(DISTINCT "CustomerID") AS unique_customers
                FROM online_retail
                WHERE EXTRACT(YEAR FROM "InvoiceDate") = :year
                  AND EXTRACT(MONTH FROM "InvoiceDate") = :month
                  AND "Quantity" > 0
                  AND "Revenue" > 0
                GROUP BY "Country"
                ORDER BY total_revenue DESC
                LIMIT :limit;
            """)

    with engine.connect() as connection:
        results = pd.read_sql(
            query,
            connection,
            params={"year": year, "month": month, "limit": limit}
        )
    return results.to_json(orient="records")


@tool
def customer_purchase_history_tool(customer_id: int) -> str:
    """Retrieve up to 100 purchases for a customer.
    Use for questions about a particular customer's orders, dates and spending.
    """
    query = text("""
                SELECT
                    "InvoiceNo",
                    "InvoiceDate",
                    SUM("Quantity") AS total_quantity,
                    SUM("Revenue") AS invoice_revenue
                FROM online_retail
                WHERE "CustomerID" = :customer_id
                  AND "Quantity" > 0
                  AND "Revenue" > 0
                GROUP BY "InvoiceNo", "InvoiceDate"
                ORDER BY "InvoiceDate" DESC
                LIMIT 100;
            """)

    with engine.connect() as connection:
        results = pd.read_sql(
            query,
            connection,
            params={"customer_id": customer_id}
        )
    return results.to_json(orient="records", date_format="iso")


@tool
def monthly_kpi_tool(year: int, month: int) -> str:
    """Calculate monthly KPIs: revenue, units, invoices, unique customers,
    average order value and revenue per customer.
    """
    query = text("""
                SELECT
                    SUM("Revenue") AS total_revenue,
                    SUM("Quantity") AS total_quantity,
                    COUNT(DISTINCT "InvoiceNo") AS total_invoices,
                    COUNT(DISTINCT "CustomerID") AS unique_customers,
                    ROUND(
                        (SUM("Revenue") /
                        NULLIF(COUNT(DISTINCT "InvoiceNo"), 0))::NUMERIC, 2
                    ) AS average_order_value,
                    ROUND(
                        (SUM("Revenue") /
                        NULLIF(COUNT(DISTINCT "CustomerID"), 0))::NUMERIC, 2
                    ) AS revenue_per_customer
                FROM online_retail
                WHERE EXTRACT(YEAR FROM "InvoiceDate") = :year
                  AND EXTRACT(MONTH FROM "InvoiceDate") = :month
                  AND "Quantity" > 0
                  AND "Revenue" > 0;
            """)

    with engine.connect() as connection:
        results = pd.read_sql(
            query,
            connection,
            params={"year": year, "month": month}
        )
    return results.to_json(orient="records")


# 2. REGISTER TOOLS AND INITIALIZE THE LANGUAGE MODEL

tools = [
    anomaly_detection_tool,
    monthly_revenue_tool,
    top_products_tool,
    customer_analytics_tool,
    country_sales_tool,
    business_summary_tool,
    repeat_customer_tool,
    monthly_product_analysis_tool,
    monthly_country_analysis_tool,
    customer_purchase_history_tool,
    monthly_kpi_tool,
]


model_name = os.getenv("OPENAI_MODEL", "gpt-6-luna")

llm = ChatOpenAI(
    model=model_name,
    temperature=0,
    reasoning_effort="none",
)

llm_with_tools = llm.bind_tools(tools)


# 3. BUILD THE LANGGRAPH AGENT


def chatbot(state: MessagesState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


tool_node = ToolNode(tools)

graph_builder = StateGraph(MessagesState)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

# MemorySaver keeps conversations in memory while this backend process runs.
memory = MemorySaver()
agent = graph_builder.compile(checkpointer=memory)


# 4. HELPER FUNCTION FOR TESTING AND API USE
def ask_agent(question: str, thread_id: str = "default") -> str:
    """Send a question to the agent and return its final text response."""
    config = {"configurable": {"thread_id": thread_id}}
    response = agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config=config,
    )
    return response["messages"][-1].content
