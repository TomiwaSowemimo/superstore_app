import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from urllib.error import URLError

@st.cache_data
def load_data():
    data = pd.read_excel("Super+Store+Data.xlsx")
    df = data.copy()
    df = df.rename(columns ={
        "Row ID": "Row_ID",
        "Order ID": "Order_ID",
        "Order Date": "Order_Date",
        "Ship Mode": "Ship_Mode",
        "Customer ID": "Customer_ID",
        "Customer Name": "Customer_Name",
        "Product ID": "Product_ID",
        "Product Name": "Product_Name",
        "Sub-Category": "Sub_Category",
        "Ship Date": "Ship_Date",

    })
    # add Year column
    df["Year"] = df["Order_Date"].dt.year
    df["Month"] = df["Order_Date"].dt.month_name()
    df["Quarter"] = df["Order_Date"].dt.quarter
    df["Month_No"] = df["Order_Date"].dt.month
    df["Year_Month"] =df["Order_Date"].dt.to_period("M").dt.to_timestamp()
    df["Shipping_Days"] = (
        df["Ship_Date"] - df["Order_Date"]
        ).dt.days
    df["Profit_Margin"] = df["Profit"] /df["Sales"]
    df["Loss"] = df["Profit"] < 0
    return df

try:
    df = load_data()
    st.title("Super Store Data Analysis")
    # st.write(df.isnull().sum()) #check for null values
    # st.write(df.dtypes) #check data types

    #filters
    filters = {
        "Year":df["Year"].unique(),
        "Month":df["Month"].unique(),
        "Ship_Mode":df["Ship_Mode"].unique(),
        "Segment":df["Segment"].unique(),
        "State":df["State"].unique(),
        "City":df["City"].unique(),
        "Category":df["Category"].unique()
    }

    # store user selection
    selected_filters ={}
    # generates multi-select widgest dynamically
    for key, options in filters.items():
        selected_filters[key] = st.sidebar.multiselect(key, options)

        #selected data filtered
        filtered_df = df.copy()

        # apply user selections to the data
        for key, selected_values in selected_filters.items():
            if selected_values:
                filtered_df = filtered_df[filtered_df[key]\
                                          .isin(selected_values)]

    #st.sidebar
    st.sidebar.multiselect("1", "Name")

    # view data
    st.dataframe(filtered_df)

    #section 2: Calculations
    total_sales = filtered_df["Sales"].sum()
    total_profit = filtered_df["Profit"].sum()
    no_orders =len(filtered_df)
    no_customers = filtered_df["Customer_ID"].nunique()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        #st.write(f"Total Sales: ${total_sales:,.2f}")
        st.metric("Total Sales", f"${total_sales:,.2f}")
    with col2:
        #st.write(f"Total Profit: ${total_profit:,.2f}")
        st.metric("Total Profit", f"${total_profit:,.2f}")
    with col3:
        #st.write(f"Number of Orders: {no_orders}")
        st.metric("Number of Orders", no_orders)
    with col4:
        st.write(f"Number of Customers: {no_customers}")
        st.metric("Number of Customers", no_customers)

#charts
    # chart data
    temp_df =(
        filtered_df.groupby("Year", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit","sum"))
        .sort_values("Year")

    )
    st.header("Year Trend - Sales and Profit")
    metric_choice =st.radio(
        "Trend Metric",
        ["Sales", "Profit"],
        horizontal=True, key="trend_metric",
    )
    trend= (
        alt.Chart(temp_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Year:O", title="Year"),
            y=alt.Y(f"{metric_choice}:Q", title=metric_choice),
            tooltip=[
                alt.Tooltip("Year:O", title="Year"),
                alt.Tooltip(f"{metric_choice}:Q", format="$,.2f")
            ]
        )
    )
    st.altair_chart(trend, use_container_width=True)
    #generate multi-select filters for

    #Chart 2
    import plotly.express as px # new
    st.header("Locatiions")

    geo_col, ship_col =st.columns([1.2,1])
    #chart data
    state_df =(
        filtered_df.groupby(["State", "Region"], as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        .sort_values("Sales", ascending=False)
        .head(15)
    )

    with geo_col:
        fig_state = px.bar(
            state_df.sort_values("Profit"), x="Profit",y="State",
            orientation ="h", color="Region",
            title="Top states by sales, ranked by profit",
            hover_data ={"Sales": ":,2f"},
        )
        fig_state.add_vline(x=0, line_dash ="dash")
        fig_state.update_layout(height=480,
                                margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_state, use_container_width=True)

    #shipping data
    ship_df =(
        filtered_df.groupby("Ship_Mode", as_index=False)
        .agg(
            Average_Shipping_Days=("Shipping_Days", "mean"),
            Sales=("Sales","sum"),
            Profit=("Profit","sum"),
            Orders=("Order_ID", "nunique"),
            )
    )
    # chart
    with ship_col:
        st.write("Operational Performace")
        ship_chart = (
            alt.Chart(ship_df).mark_bar()
            .encode(
                x=alt.X("Average_Shipping_Days:Q", 
                        title="Average shipping days"),
                y=alt.Y("Ship_Mode:N", sort="-x", title=None,
                        ) 
            )
            .properties(title="Delivery speed by ship mode", height=380)
        )
        st.altair_chart(ship_chart, use_container_width=True)

        
except Exception as a:
    st.exception(a)