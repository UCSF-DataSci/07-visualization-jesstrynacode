import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap

# Directory where CSV files are stored
directory = 'ddf--datapoints--population--by--country--age--gender--year/'

# function to categorize ages into age groups, used same groups as previous example
def categorize_age_group(df):
    bins = [0, 14, 30, 45, 65, 100]  
    labels = ['0-14', '15-30', '31-45', '46-65', '66+']
    
    if 'age' in df.columns:
        df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels, right=True)
    return df

# function to dynamically load all available countries based on filenames
def load_data(directory):
    data = {}
    country_labels = {}
    
    # Loop through the directory and find CSV files that match the pattern
    for filename in os.listdir(directory):
        if filename.endswith('.csv') and '--by--country-' in filename:
            # Extract country code from the filename
            country_code = filename.split('--by--country-')[1].split('--age--gender--year.csv')[0]
            country_labels[country_code] = country_code.upper()  # For now, we will use the country code as the label
            
            # Load the data, store in data dictionary
            filepath = os.path.join(directory, filename)
            df = pd.read_csv(filepath)
            
            # make sure year is numeric, categorize age groups
            df['year'] = pd.to_numeric(df['year'], errors='coerce')  
            df = categorize_age_group(df)
            
            data[country_code] = df
    
    return data, country_labels

# load data for all countries
data, country_labels = load_data(directory)

# convert the country labels to improve readability in the dropdown
country_options = list(country_labels.values())

# Edit Country Selection Sidebar
st.sidebar.title("Population Dashboard")
selected_countries = st.sidebar.multiselect(
    'Select 2-3 countries to compare', 
    country_options, 
    default=country_options[:3]  # Default to first 3 countries
)

# Edit Year range selection Sidebar
year_range = st.sidebar.slider('Select Year Range', min_value=1950, max_value=2020, value=(1950, 2020))

# Edit Age group selection Sidebar
age_groups = ['0-14', '15-30', '31-45', '46-65', '66+']
selected_age_groups = st.sidebar.multiselect('Select Age Groups', age_groups, default=age_groups)

# Display Population Trends in Main Section: 
st.title("Population Trends Over Time")

# Filter data based on selections (for total population, not filtered by age group)
def filter_data(data, selected_countries, year_range):
    reverse_country_labels = {v: k for k, v in country_labels.items()}
    selected_country_codes = [reverse_country_labels[c] for c in selected_countries]
    
    filtered_data = pd.DataFrame()

    for country_code in selected_country_codes:
        df_country = data[country_code]
        
        # Make sure that 'year' exists, add full country name for labeling
        if 'year' in df_country.columns:
            df_country = df_country[(df_country['year'] >= year_range[0]) & (df_country['year'] <= year_range[1])]
            df_country['country'] = country_labels[country_code]  
            filtered_data = pd.concat([filtered_data, df_country], ignore_index=True)
    
    return filtered_data

filtered_data = filter_data(data, selected_countries, year_range)

# Plot total population trends over time, this is not filtered by age group
if not filtered_data.empty:
    st.subheader("Total Population Over Time")

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Get a colormap for each country
    colors = cm.get_cmap('Set2', len(selected_countries)).colors
    country_colors = {}  # store the color of each country
    
    for i, country in enumerate(selected_countries):
        country_data = filtered_data[filtered_data['country'] == country]
        # Group by year and aggregate the population
        total_population = country_data.groupby('year')['population'].sum()
        ax.plot(total_population.index, total_population.values, label=country, color=colors[i])
        country_colors[country] = colors[i]  # Store the color used for the country

    ax.set_title("Total Population Trends Over Time")
    ax.set_xlabel("Year")
    ax.set_ylabel("Total Population")
    ax.legend(loc='upper left')
    ax.grid(True)
    st.pyplot(fig)
else:
    st.write("No data available for the selected criteria.")

# Display Data Table with Key Statistics
st.subheader("Key Population Statistics")
if not filtered_data.empty:
    stats = filtered_data.groupby('country')['population'].agg(['sum', 'mean', 'max', 'min']).reset_index()
    st.write(stats)
else:
    st.write("No statistics available for the selected criteria.")

# Part 2: Stacked Bar Chart - Demographic Shifts (one for each country, stratified by age group)
if selected_age_groups:
    st.subheader("Demographic Shifts by Age Group (Stacked Bar Chart for Each Country)")

    # Define years for comparison, used same as previous assignment
    years = [1950, 1985, 2020]

    for country in selected_countries:
        st.write(f"**{country}**")
        
        # Prepare data for each country
        country_data = filtered_data[filtered_data['country'] == country]
        percentages = {year: [] for year in years}

        # Loop through each year and calculate population percentages by age group
        for year in years:
            yearly_data = country_data[country_data['year'] == year]
            
            # Group by age group and calculate total population
            age_group_data = yearly_data.groupby('age_group')['population'].sum()
            total_population = age_group_data.sum()
            
            # Calculate the percentage of each age group and store it
            for age_group in selected_age_groups:
                population_in_group = age_group_data.get(age_group, 0)
                percentage = (population_in_group / total_population) * 100 if total_population > 0 else 0
                percentages[year].append(percentage)

        # Transpose the percentage data for plotting
        stacked_data = pd.DataFrame(percentages, index=selected_age_groups)

        # Create a color gradient based on the base color of the country
        base_color = country_colors[country]
        cmap = LinearSegmentedColormap.from_list(f"{country}_cmap", [base_color, "white"], N=len(selected_age_groups))
        gradient_colors = [cmap(i / (len(selected_age_groups) - 1)) for i in range(len(selected_age_groups))]

        # Create the stacked bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        stacked_data.T.plot(kind='bar', stacked=True, color=gradient_colors, ax=ax)

        # Add title and labels
        ax.set_title(f"Age Group Distribution for {country} Across 1950, 1985, and 2020")
        ax.set_xlabel("Year")
        ax.set_ylabel("Percentage of Total Population")
        plt.xticks(rotation=0)

        # Annotate with percentage values
        for i, year in enumerate(years):
            for j, age_group in enumerate(selected_age_groups):
                percentage = stacked_data[year][age_group]
                if percentage > 0:
                    ax.text(i, sum(stacked_data[year][:j]) + (percentage / 2), f'{percentage:.1f}%', ha='center', va='center')

        # Add legend to the upper right and format it
        ax.legend(title="Age Group", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small', title_fontsize='small')

        st.pyplot(fig)
else:
    st.write("Select age groups to see the demographic shifts.")
