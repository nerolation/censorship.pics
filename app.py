import os
import re
import dash
from datetime import datetime
from dash import  Dash, Input, Output, dcc, html, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import dash_bootstrap_components as dbc
import numpy as np
from dash import Input, Output
from plotly.subplots import make_subplots
import random

QUERY = """
SELECT {}
FROM {}
{}
"""

def build_query(select, dataset, appendix=""):
    return QUERY.format(select, dataset, appendix)
BLACK = "rgb(15, 20, 25)"
BLACK_ALPHA = "rgba(15, 20, 25, {})"

def clean_url(url):
    url = re.sub(r'https?://', '', url)
    url = re.sub(r'www\.', '', url)
    url = re.sub(r'\.[a-zA-Z]{2,}$', '', url)
    url = re.sub(r'(\.[a-zA-Z]{2,})/.*$', r'\1', url)
    return url

def get_latest_slot_stats(df_censorship, df_entity, category):
    df_cat = df_censorship[df_censorship["category"] == category]
    _df = df_entity.merge(df_cat[["entity","censoring"]], how="left", left_on=category, right_on="entity")
    _df = _df.fillna(0)
    df = _df
    agg_df = df.groupby(["timestamp", "censoring"]).agg({"slot": "sum"}).reset_index()
    agg_df["color"] = agg_df["censoring"].apply(lambda x: "#FF0000" if x == 1 else "#008000")
    agg_df["censoring"] = agg_df["censoring"].apply(lambda x: "censoring" if x == 1 else "non-censoring")
    agg_df.sort_values("censoring", inplace=True)
    agg_df = agg_df[agg_df["timestamp"] != max(agg_df["timestamp"])]
    latest_data = agg_df[agg_df['timestamp'] == agg_df['timestamp'].max()]
    total_slots = latest_data['slot'].sum()
    latest_data.loc[:,('percentage')] = (latest_data['slot'] / total_slots) * 100
    return latest_data
    
  
    
# Data preparation
def prepare_data():
    df_censorship = pd.read_csv("censorship_stats.csv").replace("Unknown", "Unknown/missed")
    
    df_relays_over_time = pd.read_csv("relays_over_time.csv")
    df_builders_over_time = pd.read_csv("builders_over_time.csv")
    df_validators_over_time = pd.read_csv("validators_over_time_censorship.csv")
    df_relay = pd.read_csv("relay_stats.csv").sort_values("all_blocks", ascending=False)
    df_builder = pd.read_csv("builder_stats.csv").sort_values("all_blocks", ascending=False)
    df_validator = pd.read_csv("validator_stats.csv").sort_values("all_blocks", ascending=False)
    df_builder["builder"] = df_builder["builder"].apply(lambda x: x[0:10]+"..." if x.startswith("0x") else x)
    
    df_relay["all_block_share"] = df_relay["all_blocks"] / df_relay.all_blocks.sum()
    df_builder["all_block_share"] = df_builder["all_blocks"] / df_builder.all_blocks.sum()
    df_validator["all_block_share"] = df_validator["all_blocks"] / df_validator.all_blocks.sum()
    
    
    dfs_over_time = [
        (df_relays_over_time, "relay"),
        (df_builders_over_time, "builder"),
        (df_validators_over_time, "validator")
    ]
    latest_slots = []
    for i, j in dfs_over_time:
        latest_slots.append(get_latest_slot_stats(df_censorship, i, j))

    latest_data_relay, latest_data_builder, latest_data_validator = tuple(latest_slots)
    
    
    def max_slot(slot):
        return int(slot.split("[")[1].split("]")[0])
    
    return (
        df_censorship,
        df_relays_over_time,
        df_builders_over_time,
        df_validators_over_time,
        latest_data_relay, 
        latest_data_builder, 
        latest_data_validator,
        df_relay,
        df_builder,
        df_validator
    )
############ Load data

(df_censorship, 
 df_relays_over_time, 
 df_builders_over_time, 
 df_validators_over_time,
 latest_data_relay, 
 latest_data_builder, 
 latest_data_validator,
 df_relay,
 df_builder,
 df_validator) = prepare_data()


############ Global variables

df_validator['validator'] = df_validator['validator'].apply(lambda x: x[:15]+"..." if len(x) > 15 else x)
df_validator["validator"] = df_validator.apply(lambda x: f'{x["validator"]} <span style="font-size:1.07vh">({x["all_block_share"]*100:.2f}%)</span>', axis=1)
df_relay['relay'] = df_relay['relay'].apply(lambda x: x[:15]+"..." if len(x) > 15 else x)
df_relay["relay"] = df_relay.apply(lambda x: f'{x["relay"]} <span style="font-size:1.07vh">({x["all_block_share"]*100:.2f}%)</span>', axis=1)
df_builder["builder"] = df_builder["builder"].apply(lambda x: x.split("(")[0] if "(" in x else x)
df_builder['builder'] = df_builder['builder'].apply(lambda x: f'{clean_url(x)}')
df_builder['builder'] = df_builder['builder'].apply(lambda x: x[:15]+"..." if len(x) > 15 else x)
df_builder["builder"] = df_builder.apply(lambda x: f'{x["builder"]} <span style="font-size:1.07vh">({x["all_block_share"]*100:.2f}%)</span>', axis=1)
relay_names = df_relay.relay.to_list()[::-1]
relay_values = df_relay.share.to_list()[::-1]
builder_names = df_builder.builder.to_list()[::-1]
builder_values = df_builder.share.to_list()[::-1]
validator_names = df_validator.validator.to_list()[::-1]
validator_values = df_validator.share.to_list()[::-1]

y_positions_relay = np.linspace(0, len(relay_names)-1, len(relay_names))  # Y-positions for bars and arrows
y_positions_builder = np.linspace(0, len(builder_names)-1, len(builder_names))  # Y-positions for bars and arrows
y_positions_validator = np.linspace(0, len(validator_names)-1, len(validator_names))  # Y-positions for bars and arrows

relay_bar_count = len(relay_names) * 10
relay_arrow_count = len(relay_names)
builder_bar_count = len(builder_names) * 10
builder_arrow_count = len(builder_names)
validator_bar_count = len(validator_names) * 10
validator_arrow_count = len(validator_names)


#########################################################

def update_censorship_bars_layout(width=801):
    if width <= 800:
        font_size = 12
        shape_delta_x = 0.02
        shape_delta_y = 0.01
    else:
        font_size = 18
        shape_delta_x = 0
        shape_delta_y = 0
        
    return dict(
        barmode='stack',
        title='',
        plot_bgcolor="#ffffff",
        height=650,
        margin=dict(l=40, r=0, t=90, b=20),
        xaxis1=dict(showticklabels=False, fixedrange =True),  # Hide x-axis labels for first subplot
        xaxis2=dict(showticklabels=False, fixedrange =True),  # Hide x-axis labels for second subplot
        xaxis3=dict(showticklabels=False, fixedrange =True),  # Hide x-axis labels for third subplot
        yaxis1=dict(showticklabels=False, fixedrange =True),  # Hide y-axis labels for first subplot
        yaxis2=dict(showticklabels=False, fixedrange =True),  # Hide y-axis labels for second subplot
        yaxis3=dict(showticklabels=False, fixedrange =True),
        showlegend=False,
        hoverlabel=dict(
            bgcolor="white",
            font_size=font_size,
            font_family="Ubuntu Mono"
        ),
        shapes=[
            # Red box for 'censoring'
            dict(
                type='rect',
                x0=0.95,
                x1=0.93-shape_delta_x,
                y0=1.1+shape_delta_y*2,
                y1=1.14+shape_delta_y,
                xref='paper',
                yref='paper',
                fillcolor='#d07070',
                line=dict(color='black', width=2),
                opacity=1,
            ),
            # Green box for 'non-censoring'
            dict(
                type='rect',
                x0=0.95,
                x1=0.93-shape_delta_x,
                y0=1.02+shape_delta_y*2,
                y1=1.06+shape_delta_y,
                xref='paper',
                yref='paper',
                fillcolor='#80bf80',
                line=dict(color='black', width=2),
                opacity=1,
            )
        ]
    )

def censorship_bars(latest_data_relay, latest_data_builder, latest_data_validator):
# Initialize subplot with 3 rows
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=(
        '<span style="font-size: 24px;font-weight:bold;">Relays</span>', 
        '<span style="font-size: 24px;font-weight:bold;">Builders</span>',
        '<span style="font-size: 24px;font-weight:bold;">Validators</span>'
    ), vertical_spacing=0.15)

    annotations = []

    # Data and rows
    data_rows = [(latest_data_relay, 'x'), (latest_data_builder, 'x2'), (latest_data_validator, 'x3')]

    for idx, (data, xref) in enumerate(data_rows):
        stack_position = 0
        for index, row in data.iterrows():
            fig.add_trace(
                go.Bar(
                    x=[row['percentage']],
                    y=[idx],
                    orientation='h',
                    name=row['censoring'],
                    marker=dict(
                        color='#d07070' if row['censoring'] == 'censoring' else '#80bf80',
                        line=dict(color='black', width=2)
                    )
                ), row=idx + 1, col=1
            )

            if row["percentage"] > 10:
                annotation_text = f'{row["percentage"]:.2f}%'
            else:
                annotation_text = f""

            annotations.append(
                dict(
                    x=stack_position + row['percentage'] / 2,
                    y=idx,
                    xref=xref,
                    yref=f'y{idx + 1}',
                    text=f'<span style="font-weight:bold;">{annotation_text}</span>',
                    showarrow=False,
                    font=dict(size=18, color="white")
                )
            )
            annotations.append(
                dict(
                    x=stack_position + row['percentage'] / 2,
                    y=idx,
                    xref=xref,
                    yref=f'y{idx + 1}',
                    text=f'<span style="font-weight:bold;">{annotation_text}</span>',
                    showarrow=False,
                    font=dict(size=10, color="white"),
                    visible=False
                )
            )

            stack_position += row['percentage']
            
    legend_annotations = [
            # Text for 'censoring'
            dict(
                x=0.91,
                y=1.15,
                xref='paper',
                yref='paper',
                text='Censoring',
                showarrow=False,
                font=dict(size=18, color="black")
            ),
            # Text for 'non-censoring'
            dict(
                x=0.91,
                y=1.07,
                xref='paper',
                yref='paper',
                text='Non-Censoring',
                showarrow=False,
                font=dict(size=18, color="black")
            )
        ]
    annotations.extend(legend_annotations)

    fig['layout']['annotations'] += tuple(annotations)

    fig.update_layout(**update_censorship_bars_layout())
    
    for trace in fig.data:
        trace.hovertemplate = "<b>%{fullData.name}:</b> %{x:.2f}%<extra></extra>"
    return fig

#########################################################
fig1_len, fig2_len, fig3_len = [1]*3
def update_layout_censorship_over_last_month(width=801):
    if width <= 800:
        font_size = 12
    else:
        font_size = 18
        
    buttons = [
        dict(label="Relays",
             method="update",
             args=[{"visible": [True for _ in range(fig1_len)] + [False for _ in range(fig2_len)] + [False for _ in range(fig3_len)]},
                   {"title": '<span style="font-size: 24px;font-weight:bold;">Censorship - Relays</span>'}]
            ),
        dict(label="Builders",
             method="update",
             args=[{"visible": [False for _ in range(fig1_len)] + [True for _ in range(fig2_len)] + [False for _ in range(fig3_len)]},
                   {"title": '<span style="font-size: 24px;font-weight:bold;">Censorship - Builders</span>'}]
            ),
        dict(label="Validators",
             method="update",
             args=[{"visible": [False for _ in range(fig1_len)] + [False for _ in range(fig2_len)] + [True for _ in range(fig3_len)]},
                   {"title": '<span style="font-size: 24px;font-weight:bold;">Censorship - Validators</span>'}]
            )
    ]

    return dict(
        xaxis_tickangle=-45,
        title='<span style="font-size: 24px;font-weight:bold;">Censorship - Relays</span>',
        xaxis_title="",
        yaxis_title="% of total slots",
        #yaxis_range = [0,100],
        #legend_title="Relay Provider",
        hovermode = "x unified",
        hoverlabel=dict(font=dict(color=BLACK, size=16)),
        #title_xanchor="left",
        #title_yanchor="auto",
        
        margin=dict(l=20, r=20, t=100, b=20),
        font=dict(
            family="Courier New, monospace",
            size=font_size,  # Set the font size here
            color=BLACK
        ),
        legend=dict(
            x=1,
            xanchor='right',
            y=1,
            yanchor='top',
            bgcolor='rgba(255, 255, 255, 0.7)'
        ),
        paper_bgcolor='#eee',
        plot_bgcolor='#ffffff',
        #yaxis=dict(fixedrange =True),
        #autosize=True, 
        height=580,
        #width=width,
        updatemenus=[
            dict(
                type="buttons",
                bgcolor= 'white',
                direction="right",
                x=0.5,
                xanchor="center",
                y=1.1,
                yanchor="top",
                buttons=buttons,
                font=dict(size= font_size)
            )
        ],
        xaxis=dict(
            showgrid=True, 
            gridwidth=1, 
            gridcolor=BLACK_ALPHA.format(0.2),
            tickfont=dict(size=font_size),
            fixedrange =True,    
            type="date"
        ),
        yaxis=dict(
            showgrid=True, 
            gridwidth=1, 
            gridcolor=BLACK_ALPHA.format(0.2),
            tickfont=dict(size=font_size),
            title_font=dict(size=font_size+2), 
            range=[0,100],
            fixedrange =True
        ),  
    )


def create_censorship_over_last_month(df_censoring, df_relays_over_time, df_builders_over_time, df_validators_over_time):
    global fig1_len, fig2_len, fig3_len
    df_relays_over_time = df_relays_over_time[
        df_relays_over_time["timestamp"] > sorted(df_relays_over_time["timestamp"].unique())[-33]
    ]
    df_relays_over_time = df_relays_over_time[df_relays_over_time["timestamp"] != max(df_relays_over_time["timestamp"])]
    df_cat = df_censoring[df_censoring["category"] == "relay"]
    _df = df_relays_over_time.merge(df_cat[["entity","censoring"]], how="left", left_on="relay", right_on="entity")
    _df = _df.fillna(0)
    df = _df
    agg_df = df.groupby(["timestamp", "censoring"]).agg({"slot": "sum"}).reset_index()
    agg_df["color"] = agg_df["censoring"].apply(lambda x: "#FF0000" if x == 1 else "#008000")
    agg_df["censoring"] = agg_df["censoring"].apply(lambda x: "censoring" if x == 1 else "non-censoring")
    agg_df.sort_values("censoring", inplace=True)
    fig1 = px.area(agg_df, 
                  x="timestamp", 
                  y="slot", 
                  color="censoring", 
                  line_group="censoring",
                  color_discrete_sequence = ["#FF0000", "#008000"],
                  title="Relays Over Time",
                  labels={'slot':'Slot Count'},
                  groupnorm="percent",
                    pattern_shape="censoring", pattern_shape_map={"censoring":"\\", "non-censoring":""},
                  )
    for trace in fig1.data:
        trace.hovertemplate = "<b>%{fullData.name}:</b> %{y:.1f}%<extra></extra>"

    ############################
    # BUILDERS

   
    df_builders_over_time = df_builders_over_time[df_builders_over_time["timestamp"] > sorted(df_builders_over_time["timestamp"].unique())[-33]]
    df_builders_over_time = df_builders_over_time[df_builders_over_time["timestamp"] != max(df_builders_over_time["timestamp"])]

    df_cat = df_censoring[df_censoring["category"] == "builder"]
    _df = df_builders_over_time.merge(df_cat[["entity","censoring"]], how="left", left_on="builder", right_on="entity")
    _df = _df.fillna(0)
    df = _df

    agg_df = df.groupby(["timestamp", "censoring"]).agg({"slot": "sum"}).reset_index()
    agg_df["color"] = agg_df["censoring"].apply(lambda x: "#FF0000" if x == 1 else "#008000")
    agg_df["censoring"] = agg_df["censoring"].apply(lambda x: "censoring" if x == 1 else "non-censoring")
    agg_df.sort_values("censoring", inplace=True)
    fig2 = px.area(agg_df, 
                  x="timestamp", 
                  y="slot", 
                  color="censoring", 
                  #line_group="relay_censoring",
                  color_discrete_sequence = ["#FF0000", "#008000"],
                  title="Builders Over Time",
                  labels={'slot':'Slot Count'},
                  groupnorm="percent" ,
                  pattern_shape="censoring", pattern_shape_map={"censoring":"/", "non-censoring":""},
                  )
    for trace in fig2.data:
        trace.hovertemplate = "<b>%{fullData.name}:</b> %{y:.1f}%<extra></extra>"
    
    ##################################7
    # VALIDATORS

    df_validators_over_time = df_validators_over_time[df_validators_over_time["timestamp"] > sorted(df_validators_over_time["timestamp"].unique())[-32]]
    df_validators_over_time = df_validators_over_time[df_validators_over_time["timestamp"] != max(df_validators_over_time["timestamp"])]

    df_cat = df_censoring[df_censoring["category"] == "validator"]
    _df = df_validators_over_time.merge(df_cat[["entity","censoring"]], how="left", left_on="validator", right_on="entity")
    _df = _df.fillna(0)
    df = _df
    agg_df = df.groupby(["timestamp", "censoring"]).agg({"slot": "sum"}).reset_index()
    agg_df["color"] = agg_df["censoring"].apply(lambda x: "#FF0000" if x == 1 else "#008000")
    agg_df["censoring"] = agg_df["censoring"].apply(lambda x: "censoring" if x == 1 else "non-censoring")

    agg_df.sort_values("censoring", inplace=True)
    fig3 = px.area(agg_df, 
                  x="timestamp", 
                  y="slot", 
                  color="censoring", 
                  #line_group="relay_censoring",
                  color_discrete_sequence = ["#FF0000", "#008000"],
                  title="Validators Over Time",
                  labels={'slot':'Slot Count'},
                  groupnorm="percent"  # Normalize the area for each relay as a percentage of the total
                  )

    for trace in fig3.data:
        trace.hovertemplate = "<b>%{fullData.name}:</b> %{y:.1f}%<extra></extra>"
    #############################
    # COMBINE PLOTS

    fig = make_subplots(rows=1, cols=1)
    for trace in fig1['data']:
        trace.visible=True
        fig.add_trace(trace)

    for trace in fig2['data']:
        trace.visible=False
        #trace.name = f"Builders: {trace.name}"
        fig.add_trace(trace)

    for trace in fig3['data']:
        trace.visible=False
        #trace.name = f"Builders: {trace.name}"
        fig.add_trace(trace)
    
    fig1_len = len(fig1["data"])
    fig2_len = len(fig2["data"])
    fig3_len = len(fig3["data"])
    fig.update_layout(**update_layout_censorship_over_last_month())
    return fig

################################################

def comparison_chart_layout(width=801, height=2400, names=None, y_positions=None):
    if width <= 800:
        font_size = 10
        hoverlabel_size = 12
    else:
        font_size = 14
        hoverlabel_size = 16
        
    
#    visible_validator = [True]*validator_bar_count + [False]*relay_bar_count + [False]*builder_bar_count + [True]*validator_arrow_count + [False]*relay_arrow_count + [False]*builder_arrow_count

#    visible_relay = [False]*validator_bar_count + [True]*relay_bar_count + [False]*builder_bar_count + [False]*validator_arrow_count + [True]*relay_arrow_count + [False]*builder_arrow_count

#    visible_builder = [False]*validator_bar_count + [False]*relay_bar_count + [True]*builder_bar_count + [False]*validator_arrow_count + [False]*relay_arrow_count + [True]*builder_arrow_count
    return dict(
        title="Overview of the last 30 days <span style='font-size:1.5vh;'>(Lido is split up in its node operators)</span>",
        margin=dict(l=20, r=20, t=0, b=0),
        xaxis=dict(
            showline=False,
            showticklabels=False,
            zeroline=False,
            fixedrange =True,
            range=[0, 1]
        ),
        yaxis=dict(
            showline=False,
            showticklabels=True,
            fixedrange =True,
            tickfont=dict(size=font_size),
            tickvals=y_positions,  # This should be the default view
            ticktext=names  # This should be the default view
        ),
        hovermode="closest",
        hoverlabel=dict(
            font_size=hoverlabel_size,
            font_family="Ubuntu Mono"
        ),
        height=height,
        barmode='stack',
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        bargap=0.4,  # Adjust this value to set the gap between bars
        font=dict(
            family="Courier New, monospace",
            size=font_size-2,  # Set the font size here
            color=BLACK
        ),
        #updatemenus=[
        #    dict(
        #        #type="buttons",
        #        bgcolor= 'white',
        #        showactive=True,
        #        x=0.1,
        #        xanchor="left",
        #        y=1.1,
        #        yanchor="top",
        #        direction="down",
        #        font=dict(size=font_size-6),
        #        #buttons=[
        #        #    dict(label="Show Validators",
        #        #         method="update",
        #        #         args=[{"visible": visible_validator},
        #        #               {"yaxis.tickvals": y_positions_validator, "yaxis.ticktext": validator_names, "height":2500,
        #        #               "yaxis.range": [min(y_positions_validator)-1, max(y_positions_validator)+1],
        #        #               }]),
        #        #    dict(label="Show Relays",
        #        #         method="update",
        #        #         args=[{"visible": visible_relay},
        #        #               {"yaxis.tickvals": y_positions_relay, "yaxis.ticktext": relay_names, "height":430,
        #        #               "yaxis.range": [min(y_positions_relay)-1, max(y_positions_relay)+1]
        #        #               }]),
        #        #    dict(label="Show Builders",
        #        #         method="update",
        #        #         args=[{"visible": visible_builder},
        #        #               {"yaxis.tickvals": y_positions_builder, "yaxis.ticktext": builder_names, "height":1500,
        #        #               "yaxis.range": [min(y_positions_builder)-1, max(y_positions_builder)+1],
        #        #               }]),
        #        #    
        #        #]
        #    )
        #]
    )
    

def comparison_chart(entity):
    global relay_values, builder_values, validator_values
    benchmark_value = 5.0  # New benchmark value
    fig = go.Figure()
    # Create gradient bars
    # Explicitly defined colors for the gradient, transitioning from red to yellow to green
    red_tone = [208, 112, 112]
    green_tone = [128, 191, 128]
    colors = [
        f"rgb({int(red_tone[0] + (green_tone[0] - red_tone[0]) * i / 9)}, \
        {int(red_tone[1] + (green_tone[1] - red_tone[1]) * i / 9)}, \
        {int(red_tone[2] + (green_tone[2] - red_tone[2]) * i / 9)})"
        for i in range(10)
    ]

    n_colors = len(colors)
    

    if entity == "validator":
        all_entities = (validator_names, y_positions_validator)
        height=25*len(all_entities[0])
    if entity == "relay":
        all_entities = (relay_names, y_positions_relay)
        height=25*len(all_entities[0])
    if entity == "builder":
        all_entities = (builder_names, y_positions_builder)
        height=25*len(all_entities[0])

    for names, y_positions  in [
        all_entities
    ]:
        for i, (name, y_pos) in enumerate(zip(names, y_positions)):
            for j, color_value in enumerate(colors):
                fig.add_trace(
                    go.Bar(
                        y=[y_pos],
                        x=[1.0 / n_colors],
                        orientation='h',
                        marker=dict(
                            color=color_value,
                        ),
                        hoverinfo='none',
                        showlegend=False,
                        visible=True
                    )
                )




    # Add arrows for each entity
    scaled_values_relay = [max(min(val / benchmark_value, 0.99), 0.01) for val in relay_values]
    scaled_values_builder = [max(min(val / 7, 0.99), 0.01) for val in builder_values]
    scaled_values_validator = [max(min(val / benchmark_value, 0.99), 0.01) for val in validator_values]


    def adjust_based_on_second_list(scaled_values, values, decrement=0.01, max_adjusting = 0.03):
        # Check for input validity
        if len(scaled_values) != len(values):
            print("Both lists should have the same length.")
            return

        # Loop over each element in scaled_values_relay
        for i, value1 in enumerate(scaled_values):
            # Nested loop for comparison
            for j, value2 in enumerate(scaled_values):
                # Check for equality but exclude self-comparison
                if value1 == value2 and values[i] < values[j]:
                    # Deduct value in relay_values at index i by decrement, but no more than max_adjusting
                    scaled_values[i] = max(scaled_values[i] - decrement, 0.01)
        return scaled_values, values



    scaled_values_relay, relay_values = adjust_based_on_second_list(scaled_values_relay, relay_values)
    scaled_values_builder, builder_values = adjust_based_on_second_list(scaled_values_builder, builder_values)
    scaled_values_validator, validator_values = adjust_based_on_second_list(scaled_values_validator, validator_values, 0.001, 0.001)


    arrow_offset = -0.3  # Offset to slightly move the arrows up


    if entity == "validator":
        all_entities_arr = ((validator_names, scaled_values_validator, y_positions_validator, validator_values),)
    if entity == "relay":
        all_entities_arr  = ((relay_names, scaled_values_relay, y_positions_relay, relay_values),)
    if entity == "builder":
        all_entities_arr  = ((builder_names, scaled_values_builder, y_positions_builder, builder_values),)
    visible = True
    
    for entity_ix, (names, scaled_values, y_positions, values) in enumerate(all_entities_arr):
        for i, (name, scaled_value, y_pos, val) in enumerate(zip(names, scaled_values, y_positions, values)):
            # Determine the color based on the scaled_value
            color_idx = int(scaled_value * (n_colors - 1))
            corresponding_bar_color = colors[color_idx]

            fig.add_trace(
                go.Scatter(
                    y=[y_pos - arrow_offset],
                    x=[scaled_value],
                    mode='markers',
                    marker=dict(
                        symbol='triangle-down',
                        size=14,
                        color='black'
                    ),
                    hovertemplate=f"<b>{val:.2f}% non-censored blocks</b><extra></extra>",
                    hoverlabel=dict(
                        font=dict(color="white"),  # Increase size of hoverlabel
                        bgcolor=corresponding_bar_color  # Set hover label background color to match scaled_value
                    ),
                    visible=True,
                    showlegend=False
                )
            )

    # Customize layout
    fig.update_layout(
        **comparison_chart_layout(801, height, all_entities[0], all_entities[1])
    )
    return fig



# Figures
def create_figures(
    df_censorship, 
    df_relays_over_time, 
    df_builders_over_time, 
    df_validators_over_time,
    latest_data_relay, 
    latest_data_builder, 
    latest_data_validator,
    df_relay,
    df_builder,
    df_validator
):
    fig_bars = censorship_bars(latest_data_relay, latest_data_builder, latest_data_validator)
    fig_over_months = create_censorship_over_last_month(
        df_censorship, df_relays_over_time, df_builders_over_time, df_validators_over_time
    )
    
    

    fig_comp_val = comparison_chart("validator")
    fig_comp_rel = comparison_chart("relay")
    fig_comp_bui = comparison_chart("builder")
    
    #fig_comparison = comparison_chart()
    return fig_bars, fig_over_months, fig_comp_val, fig_comp_rel, fig_comp_bui # fig_comparison,



############

fig_bars, fig_over_months, fig_comp_val, fig_comp_rel, fig_comp_bui = create_figures(
    df_censorship, 
    df_relays_over_time, 
    df_builders_over_time, 
    df_validators_over_time,
    latest_data_relay, 
    latest_data_builder, 
    latest_data_validator, 
    df_relay,
    df_builder,
    df_validator
)


# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:site" content="@nero_ETH">
        <meta name="twitter:title" content="Ethereum Censorship Dashboard">
        <meta name="twitter:description" content="Selected comparative visualizations on censorship on Ethereum.">
        <meta name="twitter:image" content="https://raw.githubusercontent.com/nerolation/censorship.pics/main/assets/censorship.jpg">
        <meta property="og:title" content="Censorship.pics" relay="" api="" dashboard="">
        <meta property="og:site_name" content="censorship.pics">
        <meta property="og:url" content="censorship.pics">
        <meta property="og:description" content="Selected comparative visualizations on censorship on Ethereum.">
        <meta property="og:type" content="website">
        <link rel="shortcut icon" href="https://raw.githubusercontent.com/nerolation/censorship.pics/main/assets/censorship.jpg">
        <meta property="og:image" content="https://raw.githubusercontent.com/nerolation/censorship.pics/main/assets/censorship.jpg">
        <meta name="description" content="Selected comparative visualizations on reorged blocks on Ethereum.">
        <meta name="keywords" content="Ethereum, Censorship, Dashboard">
        <meta name="author" content="Toni Wahrstätter">
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''
app.scripts.append_script({"external_url": "update_window_width.js"})
app.clientside_callback(
    "window.dash_clientside.update_window_size",
    Output('window-size-store', 'data'),
    Input('window-size-trigger', 'n_intervals')
)
app.title = 'Censorship.pics'
server = app.server

def table_styles(width):
    font_size = '20px' if width >= 800 else '10px'

    return [
        {'if': {'column_id': 'Slot Nr. in Epoch'}, 'maxWidth': '30px', 'textAlign': 'center', 'fontSize': font_size},
        {'if': {'column_id': 'Slot'}, 'textAlign': 'right', 'maxWidth': '40px', 'fontSize': font_size},
        {'if': {'column_id': 'Parent Slot'}, 'textAlign': 'center', 'maxWidth': '40px', 'fontSize': font_size},
        {'if': {'column_id': 'Val. ID'}, 'maxWidth': '30px', 'fontSize': font_size},
        {'if': {'column_id': 'Date'}, 'maxWidth': '80px', 'fontSize': font_size},
        {'if': {'column_id': 'CL Client'}, 'maxWidth': '80px', 'fontSize': font_size}
    ]



app.layout = html.Div(
    [
        dbc.Container(
        [
            # Title
            dbc.Row(html.H1("Ethereum Censorship Dashboard", style={'textAlign': 'center','marginTop': '20px'}), className="mb-4"),
            html.Div([
                dbc.Row([
                    dbc.Col(
                        html.H5(
                            ['Built with 🖤 by ', html.A('Toni Wahrstätter', href='https://twitter.com/nero_eth', target='_blank'), html.Br(), 'Underlying data from the past 30 days'],
                            className="mb-4 even-smaller-text" # Apply the class
                        ),
                        width={"size": 6, "order": 1}
                    ),
                    dbc.Col(
                        html.H5(
                            ['Check out ', html.A('tornado-warning.info', href='https://tornado-warning.info', target='_blank'), " for more stats"],
                            className="mb-4 even-smaller-text text-right",
                            style={'textAlign': 'right', "marginRight": "2vw", "marginBottom": "0px", "paddingBottom": "0px"}
                        ),
                        width={"size": 6, "order": 2}
                    )
                ], style={"marginBottom": "0px", "paddingBottom": "0px"}),
            ]),
            

            # Graphs
            dbc.Row(dbc.Col(dcc.Graph(id='graph1', figure=fig_bars), md=12, className="mb-4")),
            dbc.Row(dbc.Col(dcc.Graph(id='graph2', figure=fig_over_months), md=12, className="mb-4")),
            #dbc.Row(dbc.Col(dcc.Graph(id='graph3', figure=fig_comp_val), md=12, className="mb-4")),

           dbc.Row(
                dbc.Col(
                    [
                        dbc.Button('Validators', id='btn-a', n_clicks=0, className='mr-1', style={'fontFamily': 'Ubuntu Mono, monospace','backgroundColor': '#ddd', 'border': '1px solid #eee', 'color': 'black'}),
                        dbc.Button('Relays', id='btn-b', n_clicks=0, className='mr-1', style={'fontFamily': 'Ubuntu Mono, monospace','backgroundColor': 'white', 'border': '1px solid #eee', 'color': 'black'}),
                        dbc.Button('Builders', id='btn-c', n_clicks=0, style={'fontFamily': 'Ubuntu Mono, monospace','backgroundColor': 'white', 'border': '1px solid #eee', 'color': 'black'})

                    ],
                    width={"size": 6, "offset": 3}
                ),
                className="mb-4"
            ),
            dbc.Row(dbc.Col(html.Div(id="graph-container"))),
            dbc.Row(dbc.Col(id='dynamic-graph', md=12, className="mb-4")),


            dbc.Row(dcc.Interval(id='window-size-trigger', interval=1000, n_intervals=0, max_intervals=1)),
            dcc.Store(id='window-size-store',data={'width': 800})
        ],
        fluid=True,
             style={"maxWidth": "960px"}
    )],
    id='main-div',
    style={
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "center",
                "alignItems": "center",
                "minHight": "100vh"
            }
)


# Callbacks

#@app.callback(
#    Output('table', 'style_cell_conditional'),
#    Input('window-size-store', 'data')
#)
#def update_table_styles(window_size_data):
#    if window_size_data is None:
#        raise dash.exceptions.PreventUpdate
#
#    window_width = window_size_data['width']
#    return table_styles(window_width)
    
    
@app.callback(
    Output('main-div', 'style'),
    Input('window-size-store', 'data')
)
def update_main_div_style_dynamic(window_size_data):
    if window_size_data is None:
        raise dash.exceptions.PreventUpdate

    window_width = window_size_data['width']
    if window_width > 800:
        return {'marginRight': '110px', 'marginLeft': '110px'}
    else:
        return {}

@app.callback(
    Output('graph1', 'figure'),
    Input('window-size-store', 'data')
)
def update_layout2(window_size_data):
    if window_size_data is None:
        raise dash.exceptions.PreventUpdate
    width = window_size_data['width']
    fig_bars.update_layout(**update_censorship_bars_layout(width))
    if width <= 800:
        for ix, i in enumerate(fig_bars.layout.annotations[3:-2]):
            if ix % 2 != 0 and "%" in i.text:
                i.visible = True
            elif "%" in i.text:
                i.visible=False
        for i in fig_bars.layout.annotations[-2:]:
            i.font.size = 12
    else:
        for ix, i in enumerate(fig_bars.layout.annotations[3:-2]):
            if ix % 2 == 0 and "%" in i.text:
                i.visible = True
            elif "%" in i.text:
                i.visible=False
        for i in fig_bars.layout.annotations[-2:]:
            i.font.size = 18
    return fig_bars


@app.callback(
    Output('graph2', 'figure'),
    Input('window-size-store', 'data')
)
def update_layout1(window_size_data):
    if window_size_data is None:
        raise dash.exceptions.PreventUpdate
    width = window_size_data['width']
    fig_over_months.update_layout(**update_layout_censorship_over_last_month(width))
    if width <= 800:
        for i in fig_over_months.layout.updatemenus:
            i.font.size = 10
    return fig_over_months

#@app.callback(
#    Output('graph3', 'figure'),
#    Input('window-size-store', 'data')
#)
#def update_layout3(window_size_data):
#    if window_size_data is None:
#        raise dash.exceptions.PreventUpdate
#    width = window_size_data['width']
#    fig_comp_val.update_layout(**comparison_chart_layout(width))
#    if width <= 800:
#        for i in fig_comp_val.layout.updatemenus:
#            i.font.size = 10
#    return fig_comp_val

    
@app.callback(
    Output('dynamic-graph', 'children'),
    [
        Input('btn-a', 'n_clicks'),
        Input('btn-b', 'n_clicks'),
        Input('btn-c', 'n_clicks')
    ]
)
def update_graph3(btn_a, btn_b, btn_c):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if 'btn-a' in changed_id:
        return dcc.Graph(id='graph', figure=fig_comp_val)
    elif 'btn-b' in changed_id:
        return dcc.Graph(id='graph', figure=fig_comp_rel)
    elif 'btn-c' in changed_id:
        return dcc.Graph(id='graph', figure=fig_comp_bui)

    return dcc.Graph(id='graph', figure=fig_comp_val) 



@app.callback(
    [Output('btn-a', 'style'),
     Output('btn-b', 'style'),
     Output('btn-c', 'style')],
    [Input('btn-a', 'n_clicks'),
     Input('btn-b', 'n_clicks'),
     Input('btn-c', 'n_clicks')],
    prevent_initial_call=True
)
def update_button_style(n1, n2, n3):
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    default_style = {'backgroundColor': 'white', 'border': '1px solid #eee', 'color': 'black'}
    active_style = {'backgroundColor': '#ddd', 'border': '1px solid #eee', 'color': 'black'}
    
    if button_id == 'btn-a':
        return [active_style, default_style, default_style]
    elif button_id == 'btn-b':
        return [default_style, active_style, default_style]
    elif button_id == 'btn-c':
        return [default_style, default_style, active_style]
    else:
        return [default_style, default_style, default_style]



if __name__ == '__main__':
    #app.run_server(debug=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
