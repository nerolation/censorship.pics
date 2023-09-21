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
pd.set_option('mode.chained_assignment', None)
QUERY = """
SELECT {}
FROM {}
{}
"""

def build_query(select, dataset, appendix=""):
    return QUERY.format(select, dataset, appendix)
BLACK = "rgb(26, 25, 25)"
BLACK_ALPHA = "rgba(26, 25, 25, {})"

def clean_url(url):
    url = re.sub(r'https?://', '', url)
    url = re.sub(r'www\.', '', url)
    url = re.sub(r'\.[a-zA-Z]{2,}$', '', url)
    url = re.sub(r'(\.[a-zA-Z]{2,})/.*$', r'\1', url)
    return url

def get_latest_slot_stats_60d(df_censorship, df_entity, category):
    df_cat = df_censorship[df_censorship["category"] == category]
    _df = df_entity.merge(df_cat[["entity","censoring"]], how="left", left_on=category, right_on="entity")
    _df = _df.fillna(0)
    df = _df
    agg_df = df.groupby(["timestamp", "censoring"]).agg({"slot": "sum"}).reset_index()
    agg_df["color"] = agg_df["censoring"].apply(lambda x: "#FF0000" if x == 1 else "#008000")
    agg_df["censoring"] = agg_df["censoring"].apply(lambda x: "censoring" if x == 1 else "non-censoring")
    agg_df.sort_values("censoring", inplace=True)
    agg_df = agg_df[agg_df["timestamp"] != max(agg_df["timestamp"])]
    agg_df['timestamp'] = pd.to_datetime(agg_df['timestamp'])
    latest_data = agg_df[agg_df['timestamp'] > agg_df['timestamp'].max() -  pd.Timedelta(days=60)]
    total_slots = latest_data.groupby("timestamp")['slot'].sum().reset_index()
    latest_data = pd.merge(latest_data, total_slots, how="left", on="timestamp")
    latest_data.loc[:,('percentage')] = (latest_data['slot_x'] / latest_data['slot_y']) * 100
    latest_data = latest_data.groupby("censoring")["percentage"].mean().reset_index()
    print(60)
    print(latest_data)
    return latest_data

def get_latest_slot_stats_30d(df_censorship, df_entity, category):
    df_cat = df_censorship[df_censorship["category"] == category]
    _df = df_entity.merge(df_cat[["entity","censoring"]], how="left", left_on=category, right_on="entity")
    _df = _df.fillna(0)
    df = _df
    agg_df = df.groupby(["timestamp", "censoring"]).agg({"slot": "sum"}).reset_index()
    agg_df["color"] = agg_df["censoring"].apply(lambda x: "#FF0000" if x == 1 else "#008000")
    agg_df["censoring"] = agg_df["censoring"].apply(lambda x: "censoring" if x == 1 else "non-censoring")
    agg_df.sort_values("censoring", inplace=True)
    agg_df = agg_df[agg_df["timestamp"] != max(agg_df["timestamp"])]
    agg_df['timestamp'] = pd.to_datetime(agg_df['timestamp'])
    latest_data = agg_df[agg_df['timestamp'] > agg_df['timestamp'].max() -  pd.Timedelta(days=30)]
    total_slots = latest_data.groupby("timestamp")['slot'].sum().reset_index()
    latest_data = pd.merge(latest_data, total_slots, how="left", on="timestamp")
    latest_data.loc[:,('percentage')] = (latest_data['slot_x'] / latest_data['slot_y']) * 100
    latest_data = latest_data.groupby("censoring")["percentage"].mean().reset_index()
    print(30)
    print(latest_data)
    return latest_data

def get_latest_slot_stats_14d(df_censorship, df_entity, category):
    df_cat = df_censorship[df_censorship["category"] == category]
    _df = df_entity.merge(df_cat[["entity","censoring"]], how="left", left_on=category, right_on="entity")
    _df = _df.fillna(0)
    df = _df
    agg_df = df.groupby(["timestamp", "censoring"]).agg({"slot": "sum"}).reset_index()
    agg_df["color"] = agg_df["censoring"].apply(lambda x: "#FF0000" if x == 1 else "#008000")
    agg_df["censoring"] = agg_df["censoring"].apply(lambda x: "censoring" if x == 1 else "non-censoring")
    agg_df.sort_values("censoring", inplace=True)
    agg_df = agg_df[agg_df["timestamp"] != max(agg_df["timestamp"])]
    agg_df['timestamp'] = pd.to_datetime(agg_df['timestamp'])
    latest_data = agg_df[agg_df['timestamp'] > agg_df['timestamp'].max() -  pd.Timedelta(days=14)]
    total_slots = latest_data.groupby("timestamp")['slot'].sum().reset_index()
    latest_data = pd.merge(latest_data, total_slots, how="left", on="timestamp")
    latest_data.loc[:,('percentage')] = (latest_data['slot_x'] / latest_data['slot_y']) * 100
    latest_data = latest_data.groupby("censoring")["percentage"].mean().reset_index()
    print(14)
    print(latest_data)    
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
    
    bars_over_time_validator = pd.read_csv("validator_censorship_share.csv").iloc[120:]
    bars_over_time_relay = pd.read_csv("relay_censorship_share.csv").iloc[120:]
    bars_over_time_builder = pd.read_csv("builder_censorship_share.csv").iloc[120:]
    
    
    dfs_over_time = [
        (df_relays_over_time, "relay"),
        (df_builders_over_time, "builder"),
        (df_validators_over_time, "validator")
    ]
    latest_slots_60d = []
    latest_slots_30d = []
    latest_slots_14d = []
    for i, j in dfs_over_time:
        latest_slots_60d.append(get_latest_slot_stats_60d(df_censorship, i, j))
        latest_slots_30d.append(get_latest_slot_stats_30d(df_censorship, i, j))
        latest_slots_14d.append(get_latest_slot_stats_14d(df_censorship, i, j))

    latest_data_relay_60d, latest_data_builder_60d, latest_data_validator_60d = tuple(latest_slots_60d)
    latest_data_relay_30d, latest_data_builder_30d, latest_data_validator_30d = tuple(latest_slots_30d)
    latest_data_relay_14d, latest_data_builder_14d, latest_data_validator_14d = tuple(latest_slots_14d)
    
    
    def max_slot(slot):
        return int(slot.split("[")[1].split("]")[0])
    
    return (
        df_censorship,
        df_relays_over_time,
        df_builders_over_time,
        df_validators_over_time,
        latest_data_relay_60d,
        latest_data_builder_60d,
        latest_data_validator_60d,
        latest_data_relay_30d,
        latest_data_builder_30d,
        latest_data_validator_30d,
        latest_data_relay_14d,
        latest_data_builder_14d,
        latest_data_validator_14d,
        df_relay,
        df_builder,
        df_validator,
        bars_over_time_validator,
        bars_over_time_relay,
        bars_over_time_builder
    )
############ Load data

(df_censorship, 
 df_relays_over_time, 
 df_builders_over_time, 
 df_validators_over_time,
 latest_data_relay_60d,
 latest_data_builder_60d,
 latest_data_validator_60d, 
 latest_data_relay_30d,
 latest_data_builder_30d,
 latest_data_validator_30d,
 latest_data_relay_14d,
 latest_data_builder_14d,
 latest_data_validator_14d,
 df_relay,
 df_builder,
 df_validator,
 bars_over_time_validator,
 bars_over_time_relay,
 bars_over_time_builder) = prepare_data()


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
        #title=f'OFAC Compliance <span style="font-size:{font_size-4}> (last 30 days)</span>',
        plot_bgcolor="#f1f2f6",
        dragmode = False,
        paper_bgcolor= "#f1f2f6",
        height=430,
        #title_font_size = font_size+5,
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
            font_family="Ubuntu Mono, monospace"
        ),
        font=dict(
            family="Ubuntu Mono, monospace",
            #size=18,  # Set the font size here
            color="#262525"
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
                line=dict(color='#262525', width=2),
                opacity=1,
            ),
            # Green box for 'non-censoring'
            dict(
                type='rect',
                x0=0.95,
                x1=0.93-shape_delta_x,
                y0=1.02+shape_delta_y*2,
                y1=1.06+shape_delta_y*1,
                xref='paper',
                yref='paper',
                fillcolor='#80bf80',
                line=dict(color='#262525', width=2),
                opacity=1,
            )
        ]
    )

def censorship_bars(latest_data_relay, latest_data_builder, latest_data_validator):
# Initialize subplot with 3 rows
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=(
        '<span style="font-size: 24px;font-weight:bold;">Validators</span>',
        '<span style="font-size: 24px;font-weight:bold;">Relays</span>', 
        '<span style="font-size: 24px;font-weight:bold;">Builders</span>'
    ), vertical_spacing=0.15)

    annotations = []

    # Data and rows
    data_rows = [(latest_data_validator, 'x3'),(latest_data_relay, 'x'), (latest_data_builder, 'x2')]

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
                        line=dict(color='#262525', width=2)
                    )
                ), row=idx + 1, col=1
            )

            if row["percentage"] > 10:
                if row["percentage"] < 12:
                    annotation_text = f'{row["percentage"]:.0f}%'
                else:
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
                    font=dict(size=12, color="white"),
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
                font=dict(size=18, color="#262525")
            ),
            # Text for 'non-censoring'
            dict(
                x=0.91,
                y=1.07,
                xref='paper',
                yref='paper',
                text='Non-Censoring',
                showarrow=False,
                font=dict(size=18, color="#262525")
            )
        ]
    annotations.extend(legend_annotations)

    fig['layout']['annotations'] += tuple(annotations)

    fig.update_layout(**update_censorship_bars_layout())
    
    for trace in fig.data:
        trace.hovertemplate = "<b>%{fullData.name}:</b> %{x:.2f}%<extra></extra>"
    return fig


def bars_over_time_layout(width=801):
    if width <= 800:
        font_size = 12
    else:
        font_size = 18
    buttons = [
        dict(label=f"Validators",
             method="update",
             args=[
                 {"visible": [True, True, False, False, False, False]},
                   {"title": f'<span style="font-size: {font_size+2}px;font-weight:bold;">Censorship - Validators</span>'}]
            ),
        dict(label=f"Relays",
             method="update",
             args=[{"visible": [False, False, True, True, False, False]},
                   {"title": f'<span style="font-size: {font_size+2}px;font-weight:bold;">Censorship - Relays</span>'}]
            ),
        dict(label=f"Builders",
             method="update",
             args=[{"visible": [False, False, False, False, True, True]},
                   {"title": f'<span style="font-size: {font_size+2}px;font-weight:bold;">Censorship - Builders</span>'}]
            )
    ]
    return dict(
        margin=dict(l=20, r=20, t=120, b=0),
        title=f'<span style="font-size: {font_size+2}px;font-weight:bold;">Censorship - Validators</span>',
        font=dict(
            family="Courier New, monospace",
            size=font_size-2,  # Set the font size here
            color="#262525"
        ),
        hovermode="x unified",
        height=400,
        yaxis_title="% of total slots",
        
        hoverlabel=dict(font=dict(color=BLACK, size=font_size)),
        #barmode='stack',
        showlegend=True,
        plot_bgcolor='white',
        dragmode = False,
        paper_bgcolor= "#f1f2f6",
        legend=dict(
            x=1,
            font=dict(size=font_size-2),
            xanchor='right',
            y=1,
            yanchor='top',
            bgcolor='rgba(255, 255, 255, 0.7)'
        ),
        #bargap=-0.01,  
        updatemenus=[
            dict(
                type="buttons",
                bgcolor= 'white',
                direction="right",
                x=0.5,
                xanchor="center",
                y=1.15,
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
            title_font=dict(size=font_size-2), 
            range=[0,100],
            fixedrange =True
        ),  
    )



def bars_over_time(dfs, entities):
    fig = go.Figure()
    visible=True
    for df, entity in zip(dfs, entities):
        all_entities = df['censoring'].unique()
        height = 400
        prev = None
        prev_values = {}  # Store previous values here for hover template

        for ix, censor_type in enumerate(all_entities[::-1]):
            sub_df = df[df['censoring'] == censor_type].copy()  # Copy to avoid SettingWithCopyWarning
            individual_values = sub_df['Share_of_Blocks'].copy()  # Store individual values

            if ix == 0:
                prev = individual_values
            else:
                sub_df['Share_of_Blocks'] += prev.values
                prev = sub_df['Share_of_Blocks']

            prev_values[censor_type] = individual_values  # Store the individual values

            fig.add_trace(
                go.Scatter(
                    x=sub_df['date'],
                    y=sub_df['Share_of_Blocks'],
                    name=censor_type,
                    fill='tonexty',
                    mode='lines',
                    line_shape='hv',
                    marker=dict(
                        color="#FF0000" if censor_type == 'censoring' else "#008000",
                       
                    ),
                    fillpattern = dict(shape="\\") if censor_type == 'censoring' else None,
                    visible=visible,
                    customdata=individual_values,  # Include custom data
                    hovertemplate="<b>%{fullData.name}:</b> %{customdata:.1f}%<extra></extra>"
                )
            )
        visible=False
    layout = bars_over_time_layout()
    fig.update_layout(**layout)
    return fig

#########################################################
fig1_len, fig2_len, fig3_len = [2]*3
def update_layout_censorship_over_last_month(width=801):
    if width <= 800:
        font_size = 12
    else:
        font_size = 18
        
    buttons = [
        dict(label="Validators",
             method="update",
             args=[
                 {"visible": [True for _ in range(fig1_len)] + [False for _ in range(fig2_len)] + [False for _ in range(fig3_len)]},
                   {"title": f'<span style="font-size: {font_size+2}px;font-weight:bold;">Censorship - Validators (last month)</span>'}]
            ),
        dict(label="Relays",
             method="update",
             args=[{"visible": [False for _ in range(fig1_len)] + [True for _ in range(fig2_len)] + [False for _ in range(fig3_len)]},
                   {"title": f'<span style="font-size: {font_size+2}px;font-weight:bold;">Censorship - Relays (last month)</span>'}]
            ),
        dict(label="Builders",
             method="update",
             args=[{"visible": [False for _ in range(fig1_len)] + [False for _ in range(fig2_len)] + [True for _ in range(fig3_len)]},
                   {"title": f'<span style="font-size: {font_size+2}px;font-weight:bold;">Censorship - Builders (last month)</span>'}]
            )
    ]

    return dict(
        xaxis_tickangle=-45,
        title=f'<span style="font-size: {font_size+2}px;font-weight:bold;">Censorship - Relays (last month)</span>',
        xaxis_title="",
        yaxis_title="% of total slots",
        #yaxis_range = [0,100],
        #legend_title="Relay Provider",
        hovermode = "x unified",
        hoverlabel=dict(font=dict(color=BLACK, size=font_size)),
        #title_xanchor="left",
        #title_yanchor="auto",
        dragmode = False,
        margin=dict(l=20, r=20, t=120, b=20),
        font=dict(
            family="Courier New, monospace",
            size=font_size,  # Set the font size here
            color=BLACK
        ),
        legend=dict(
            x=1,
            xanchor='right',
            y=1,
            font=dict(size=font_size-2),
            yanchor='top',
            bgcolor='rgba(255, 255, 255, 0.7)'
        ),
        paper_bgcolor= "#f1f2f6",
        plot_bgcolor='#ffffff',
        #yaxis=dict(fixedrange =True),
        #autosize=True, 
        height=500,
        #width=width,
        updatemenus=[
            dict(
                type="buttons",
                bgcolor= 'white',
                direction="right",
                x=0.5,
                xanchor="center",
                y=1.15,
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
            title_font=dict(size=font_size-2), 
            range=[0,100],
            fixedrange =True
        ),  
    )


def create_censorship_over_last_month(bars_over_time_relay, bars_over_time_builder, bars_over_time_validator):
    global fig1_len, fig2_len, fig3_len
    
    bars_over_time_relay = bars_over_time_relay[
        bars_over_time_relay["date"] > sorted(bars_over_time_relay["date"].unique())[-33]
    ]
    bars_over_time_relay["color"] = bars_over_time_relay["censoring"].apply(lambda x: "#FF0000" if x == "non-censoring" else "#008000")
    bars_over_time_relay.sort_values("censoring", inplace=True)
    
    fig1 = px.area(bars_over_time_relay, 
                  x="date", 
                  y="Share_of_Blocks", 
                  color="censoring", 
                  line_group="censoring",
                  color_discrete_sequence = ["#FF0000", "#008000"],
                  title="Relays Over Time",
                  labels={'Share_of_Blocks':'Slot Count'},
                  groupnorm="percent",
                    pattern_shape="censoring", pattern_shape_map={"censoring":"\\", "non-censoring":""},
                  )
    for trace in fig1.data:
        trace.hovertemplate = "<b>%{fullData.name}:</b> %{y:.1f}%<extra></extra>"

    ############################
    # BUILDERS

   
    bars_over_time_builder = bars_over_time_builder[
        bars_over_time_builder["date"] > sorted(bars_over_time_builder["date"].unique())[-33]
    ]
    
    
    bars_over_time_builder["color"] = bars_over_time_builder["censoring"].apply(lambda x: "#FF0000" if x == "non-censoring" else "#008000")
    bars_over_time_builder.sort_values("censoring", inplace=True)
    fig2 = px.area(bars_over_time_builder, 
                  x="date", 
                  y="Share_of_Blocks", 
                  color="censoring", 
                  line_group="censoring",
                  color_discrete_sequence = ["#FF0000", "#008000"],
                  title="Builders Over Time",
                  labels={'Share_of_Blocks':'Slot Count'},
                  groupnorm="percent" ,
                  pattern_shape="censoring", pattern_shape_map={"censoring":"\\", "non-censoring":""},
                  )
    for trace in fig2.data:
        trace.hovertemplate = "<b>%{fullData.name}:</b> %{y:.1f}%<extra></extra>"
    
    ##################################7
    # VALIDATORS

    bars_over_time_validator = bars_over_time_validator[
        bars_over_time_validator["date"] > sorted(bars_over_time_validator["date"].unique())[-33]
    ]
    bars_over_time_validator.sort_values("censoring", inplace=True)
    bars_over_time_validator["color"] = bars_over_time_validator["censoring"].apply(lambda x: "#FF0000" if x == "non-censoring" else "#008000")
    fig3 = px.area(bars_over_time_validator, 
                  x="date", 
                  y="Share_of_Blocks", 
                  color="censoring", 
                  #line_group="relay_censoring",
                  color_discrete_sequence = ["#FF0000", "#008000"],
                  title="Validators Over Time",
                  labels={'Share_of_Blocks':'Slot Count'},
                  groupnorm="percent",
                  pattern_shape="censoring", pattern_shape_map={"censoring":"\\", "non-censoring":""},
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
        #title="Overview of the last 30 days <span style='font-size:1.5vh;'>(Lido is split up in its node operators)</span>",
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
        dragmode = False,
        barmode='stack',
        showlegend=False,
        plot_bgcolor='#f1f2f6',
        paper_bgcolor= "#f1f2f6",
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
        height=30*len(all_entities[0])
    if entity == "relay":
        all_entities = (relay_names, y_positions_relay)
        height=30*len(all_entities[0])
    if entity == "builder":
        all_entities = (builder_names, y_positions_builder)
        height=30*len(all_entities[0])

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
                        color='#262525'
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
    latest_data_relay_60d,
    latest_data_builder_60d,
    latest_data_validator_60d,
    latest_data_relay_30d,
    latest_data_builder_30d,
    latest_data_validator_30d,
    latest_data_relay_14d,
    latest_data_builder_14d,
    latest_data_validator_14d,
    df_relay,
    df_builder,
    df_validator,
    bars_over_time_validator,
    bars_over_time_relay,
    bars_over_time_builder
):
    fig_bars_60d = censorship_bars(latest_data_relay_60d, latest_data_builder_60d, latest_data_validator_60d)
    fig_bars_30d = censorship_bars(latest_data_relay_30d, latest_data_builder_30d, latest_data_validator_30d)
    fig_bars_14d = censorship_bars(latest_data_relay_14d, latest_data_builder_14d, latest_data_validator_14d)
    fig_over_months = create_censorship_over_last_month(
        bars_over_time_validator, bars_over_time_relay, bars_over_time_builder
    )
    
    

    fig_comp_val = comparison_chart("validator")
    fig_comp_rel = comparison_chart("relay")
    fig_comp_bui = comparison_chart("builder")
    
    fig_bars_over_time = bars_over_time(
        [bars_over_time_validator, bars_over_time_relay, bars_over_time_builder], 
        ["validator", "relay", "builder"]
    )
    
    #fig_comparison = comparison_chart()
    return (fig_bars_60d, fig_bars_30d, fig_bars_14d, fig_over_months, fig_comp_val, fig_comp_rel, fig_comp_bui, fig_bars_over_time) # fig_comparison,



############

fig_bars_60d, fig_bars_30d, fig_bars_14d, fig_over_months, fig_comp_val, fig_comp_rel, fig_comp_bui,fig_bars_over_time= create_figures(
    df_censorship, 
    df_relays_over_time, 
    df_builders_over_time, 
    df_validators_over_time,
    latest_data_relay_60d,
    latest_data_builder_60d,
    latest_data_validator_60d,
    latest_data_relay_30d,
    latest_data_builder_30d,
    latest_data_validator_30d,
    latest_data_relay_14d,
    latest_data_builder_14d,
    latest_data_validator_14d,
    df_relay,
    df_builder,
    df_validator,
    bars_over_time_validator,
    bars_over_time_relay,
    bars_over_time_builder
)


# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-NWK5CR17RH"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());

          gtag('config', 'G-NWK5CR17RH');
        </script>
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
            dbc.Row(html.H1("Ethereum Censorship Dashboard", style={'textAlign': 'center', 'marginTop': '20px', 'color': '#2c3e50', 'fontFamily': 'Ubuntu Mono, monospace', 'fontWeight': 'bold'}), className="mb-4"),
            
            html.Div([
                dbc.Row([
                    dbc.Col(
                        html.H5(
                             ['Built with 🖤 by ', html.A('Toni Wahrstätter', href='https://twitter.com/nero_eth', target='_blank'), html.Br(), ''],
                            className="mb-4 even-smaller-text", # Apply the class
                            style={'color': '#262525', 'fontFamily': 'Ubuntu Mono, monospace'}
                        ),
                        width={"size": 6, "order": 1}
                    ),
                    dbc.Col(
                        html.H5(
                            ['Check out ', html.A('tornado-warning.info', href='https://tornado-warning.info', target='_blank'), ' for additional stats', html.Br(), f'Latest data timestamp: {bars_over_time_validator["date"].max()}'],
                            className="mb-4 even-smaller-text text-right",
                            style={'textAlign': 'right', "marginRight": "2vw", "marginBottom": "0px", "paddingBottom": "0px", 'color': '#262525', 'fontFamily': 'Ubuntu Mono, monospace'}
                        ),
                        width={"size": 6, "order": 2}
                    )
                ], className="animated fadeInUp", style={"marginBottom": "0px", "paddingBottom": "0px", 'background-color': '#ecf0f1', 'fontFamily': 'Ubuntu Mono, monospace'}),
            ]),
            
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H4("What for?", style={'textAlign': 'left', 'color': '#2c3e50', 'fontFamily': 'Ubuntu Mono, monospace'}),
                        dcc.Markdown("""
**Censorship resistance** is one of the **core values of Ethereum**. Today, users can be censored at **different layers** of the stack. **Builders** can exclusively build blocks that don't contain certain transactions, **relays** can refuse relaying them, and **validators** can build local blocks that strictly exclude certain entities or only connect to censoring relays. Today, with almost 95% of MEV-Boost adoption, the network's minimum censorship is the **maximum** of all these layers. **Ultimately, validators can impact censorship. Local block building prevents from contributing to censorship through MEV-Boost.**
""", style={'textAlign': 'left', 'color': '#262525', 'fontFamily': 'Ubuntu Mono, monospace'}),
                    ], className="mb-2 even-even-smaller-text", md=6),

                    dbc.Col([
                        html.H4("Methodology", style={'textAlign': 'left', 'color': '#2c3e50', 'fontFamily': 'Ubuntu Mono, monospace'}),
                         dcc.Markdown("""**Entities** are labeled as 'censoring' if they **produce significantly low numbers** of blocks with OFAC-sanctioned transactions within a time window of 30 days, provided they have a sufficiently large block sample (>100) for evaluation. By comparing an entity's non-censored block rate with half of the average for the same time frame, a quite clear categorization can be achieved. For reporting realistic values, every transaction (incl. every trace) is analysed to determine if a block contains a OFAC-sanctionable offense or not. 
                              """, style={'textAlign': 'left', 'color': '#262525','fontFamily': 'Ubuntu Mono, monospace'}),
                    ], className="mb-2 even-even-smaller-text", md=6)
                ])
            ], className="mb-2 p-3 rounded", style={'background-color': '#ecf0f1'}),
          
            dbc.Row([html.H5("OFAC Compliance", style={'textAlign': 'left', 'marginTop': '1vh','marginLeft': '2%', 'color': '#2c3e50', 'fontFamily': 'Ubuntu Mono, monospace', 'fontWeight': 'bold'})], className="customheader mb-0"),
            dbc.Row(
                dbc.Col(
                    [
                        dbc.Button('60 days', id='btn-cc', n_clicks=0, className='mr-1', style={'fontFamily': 'Ubuntu Mono, monospace','backgroundColor': 'white', 'border': '1px solid #eee', 'color': '#262525'}),
                        dbc.Button('30 days', id='btn-aa', n_clicks=0, className='mr-1', style={'fontFamily': 'Ubuntu Mono, monospace','backgroundColor': '#ddd', 'border': '1px solid #eee', 'color': '#262525'}),
                        dbc.Button('14 days', id='btn-bb', n_clicks=0, className='mr-1', style={'fontFamily': 'Ubuntu Mono, monospace','backgroundColor': 'white', 'border': '1px solid #eee', 'color': '#262525'}),
                        
                       
                    ],className="d-flex justify-content-end",
                    style={"marginRight": "3vw"}
                ),
                style={"textAlign": "right !important"},
                className="mb-4", id="buttons-first-fig"
            ),
            # Graphs with smooth transitions
            #dbc.Row(dbc.Col(html.Div(id="graph-container2")), style={"paddingBottom": "20px"}),
            dbc.Row(dbc.Col(id='graph1', md=12, className="mb-4")),
            
            #dbc.Row(dbc.Col(dcc.Graph(id='graph11', figure=fig_bars_60d), md=12, className="mb-4 animated fadeIn")),
            #dbc.Row(dbc.Col(dcc.Graph(id='graph12', figure=fig_bars_30d), md=12, className="mb-4 animated fadeIn")),
            dbc.Row(dbc.Col(dcc.Graph(id='graph3', figure=fig_bars_over_time), md=12, className="mb-4 animated fadeIn")),
            dbc.Row(dbc.Col(dcc.Graph(id='graph2', figure=fig_over_months), md=12, className="mb-4 animated fadeIn")),
            
            dbc.Row([html.H5("Censorship-Meter", style={'textAlign': 'left', 'marginTop': '1vh','marginLeft': '2%', 'color': '#2c3e50', 'fontFamily': 'Ubuntu Mono, monospace', 'fontWeight': 'bold'}),html.H6(" (last 30 days)", style={'textAlign': 'left','marginLeft': '2%', 'color': '#2c3e50', 'fontFamily': 'Ubuntu Mono, monospace', 'fontWeight': 'bold'})], className="customheader mb-0"),
            dbc.Row(
                dbc.Col(
                    [
                        dbc.Button('Validators', id='btn-a', n_clicks=0, className='mr-1', style={'fontFamily': 'Ubuntu Mono, monospace','backgroundColor': 'white', 'border': '1px solid #eee', 'color': '#262525'}),
                        dbc.Button('Relays', id='btn-b', n_clicks=0, className='mr-1', style={'fontFamily': 'Ubuntu Mono, monospace','backgroundColor': '#ddd', 'border': '1px solid #eee', 'color': '#262525'}),
                        dbc.Button('Builders', id='btn-c', n_clicks=0, style={'fontFamily': 'Ubuntu Mono, monospace','backgroundColor': 'white', 'border': '1px solid #eee', 'color': '#262525'})
                    ],
                    className="d-flex justify-content-end",
                    style={"marginRight": "3vw"}
                ),
                className="mb-4", id="buttons-last-fig"
            ),
            dbc.Row(dbc.Col(html.Div(id="graph-container")), style={"paddingBottom": "20px"}),
            dbc.Row(dbc.Col(id='dynamic-graph', md=12, className="mb-4")),
            
            html.Div([
                html.H4('Useful Links:', style={'color': '#262525','marginLeft':'10px'}),
                html.Ul([
                    html.Li([
                        html.A('PBS censorship-resistance alternatives', href='https://notes.ethereum.org/@fradamt/H1TsYRfJc', target='_blank', style={'color': '#262525'}),
                        html.Span(" by Francesco – Oct 2022", style={'color': '#262525'})
                    ]),
                    html.Li([
                        html.A('Forward inclusion list', href='https://notes.ethereum.org/@fradamt/forward-inclusion-lists', target='_blank', style={'color': '#262525'}),
                        html.Span(" by Francesco – Oct 2022", style={'color': '#262525'})
                    ]),
                    html.Li([
                        html.A('Censorship Résistance & PBS', href='https://www.youtube.com/watch?v=XZJcZ05d-Wo', target='_blank', style={'color': '#262525'}),
                        html.Span(" by Justin – Sept 2022", style={'color': '#262525'})
                    ]),
                    html.Li([
                        html.A('How much can we constrain builders without bringing back heavy burdens to proposers?', href='https://ethresear.ch/t/how-much-can-we-constrain-builders-without-bringing-back-heavy-burdens-to-proposers/13808', target='_blank', style={'color': '#262525'}),
                        html.Span(" by Vitalik – Oct 2022", style={'color': '#262525'})
                    ]),
                    html.Li([
                        html.A('State of research: increasing censorship resistance of transactions under proposer/builder separation (PBS)', href='https://notes.ethereum.org/@vbuterin/pbs_censorship_resistance', target='_blank', style={'color': '#262525'}),
                        html.Span(" by Vitalik – Jan 2022", style={'color': '#262525'})
                    ]),
                    html.Li([
                        html.A('No free lunch – a new inclusion list design', href='https://ethresear.ch/t/no-free-lunch-a-new-inclusion-list-design/16389', target='_blank', style={'color': '#262525'}),
                        html.Span(" by Vitalik and Mike – Aug 2023", style={'color': '#262525'})
                    ]),
                    html.Li([
                        html.A('Cumulative, Non-Expiring Inclusion Lists', href='https://ethresear.ch/t/cumulative-non-expiring-inclusion-lists/16520', target='_blank', style={'color': '#262525'}),
                        html.Span(" by Toni – Aug 2023", style={'color': '#262525'})
                    ]),                    
                ])
            ], style={
                'backgroundColor': '#f1f2f6',
                'color': '#262525',
                'textAlign': 'left',
                'paddingTop': '30px',
                
            }),

            dbc.Row(dcc.Interval(id='window-size-trigger', interval=1000, n_intervals=0, max_intervals=1)),
            dcc.Store(id='window-size-store', data={'width': 800})
        ],
        fluid=True,
        style={"maxWidth": "960px", 'background-color': '#f1f2f6'}
    )],
    id='main-div',
    style={
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "center",
        "alignItems": "center",
        "minHeight": "100vh",
        'background-color': '#f1f2f6'
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

#@app.callback(
#    Output('graph1', 'figure'),
#    Input('window-size-store', 'data')
#)
#def update_layout3(window_size_data):
#    if window_size_data is None:
#        raise dash.exceptions.PreventUpdate
#    width = window_size_data['width']
#    fig_bars.update_layout(**update_censorship_bars_layout(width))
#    for i, annotation in enumerate(fig_bars.layout.annotations):
#        annotation_dict = annotation.to_plotly_json()
#        if '24px' in annotation_dict['text']:
#            annotation_dict['text'] = annotation_dict['text'].replace('24px', '14px')
#            fig_bars.layout.annotations[i].update(annotation_dict)
#    if width <= 800:
#        for ix, i in enumerate(fig_bars.layout.annotations[3:-2]):
#            if ix % 2 != 0 and "%" in i.text:
#                i.visible = True
#            elif "%" in i.text:
#                i.visible=False
#        for i in fig_bars.layout.annotations[-2:]:
#            i.font.size = 12
#        fig_bars.layout.annotations[-1].y += 0.01
#    else:
#        for ix, i in enumerate(fig_bars.layout.annotations[3:-2]):
#            if ix % 2 == 0 and "%" in i.text:
#                i.visible = True
#            elif "%" in i.text:
#                i.visible=False
#        for i in fig_bars.layout.annotations[-2:]:
#            i.font.size = 18
#    return fig_bars


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

@app.callback(
    Output('graph3', 'figure'),
    Input('window-size-store', 'data')
)
def update_layout2(window_size_data):
    if window_size_data is None:
        raise dash.exceptions.PreventUpdate
    width = window_size_data['width']
    fig_bars_over_time.update_layout(**bars_over_time_layout(width=width))
    if width <= 800:
        for i in fig_bars_over_time.layout.updatemenus:
            i.font.size = 10
    return fig_bars_over_time

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
def update_graph4(btn_a, btn_b, btn_c):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if 'btn-a' in changed_id:
        return dcc.Graph(id='graph', figure=fig_comp_val)
    elif 'btn-b' in changed_id:
        return dcc.Graph(id='graph', figure=fig_comp_rel)
    elif 'btn-c' in changed_id:
        return dcc.Graph(id='graph', figure=fig_comp_bui)

    return dcc.Graph(id='graph', figure=fig_comp_rel) 

@app.callback(
    Output('graph1', 'children'),
    [
        Input('btn-aa', 'n_clicks'),
        Input('btn-bb', 'n_clicks'),
        Input('btn-cc', 'n_clicks'),
        Input('window-size-store', 'data')
    ]
)
def update_graph3(btn_a, btn_b,  btn_c, window_size_data):
    if window_size_data is None:
        raise dash.exceptions.PreventUpdate
    width = window_size_data['width']
    
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    print(changed_id)
    if 'btn-cc' in changed_id:
        fig_bars = fig_bars_60d
    elif 'btn-bb' in changed_id:
        fig_bars = fig_bars_14d
    else:
        fig_bars = fig_bars_30d
    
    
    fig_bars.update_layout(**update_censorship_bars_layout(width))
    for i, annotation in enumerate(fig_bars.layout.annotations):
        annotation_dict = annotation.to_plotly_json()
        if '24px' in annotation_dict['text']:
            annotation_dict['text'] = annotation_dict['text'].replace('24px', '14px')
            fig_bars.layout.annotations[i].update(annotation_dict)
    if width <= 800:
        for ix, i in enumerate(fig_bars.layout.annotations[3:-2]):
            if ix % 2 != 0 and "%" in i.text:
                i.visible = True
            elif "%" in i.text:
                i.visible=False
        for i in fig_bars.layout.annotations[-2:]:
            i.font.size = 12
        fig_bars.layout.annotations[-1].y += 0.01
    else:
        for ix, i in enumerate(fig_bars.layout.annotations[3:-2]):
            if ix % 2 == 0 and "%" in i.text:
                i.visible = True
            elif "%" in i.text:
                i.visible=False
        for i in fig_bars.layout.annotations[-2:]:
            i.font.size = 18
    
    

    return dcc.Graph(id='graph123', figure=fig_bars) 



@app.callback(
    [Output('btn-a', 'style'),
     Output('btn-b', 'style'),
     Output('btn-c', 'style')],
    [Input('btn-a', 'n_clicks'),
     Input('btn-b', 'n_clicks'),
     Input('btn-c', 'n_clicks'),
     Input('window-size-store', 'data')],
    prevent_initial_call=False
)
def update_button_style(n1, n2, n3, window_size_data):
    width = window_size_data['width']
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if width <= 800:
        default_style = {'backgroundColor': 'white', 'border': '1px solid #eee', 'color': '#262525', 'fontSize': '9px'}
        active_style = {'backgroundColor': '#ddd', 'border': '1px solid #eee', 'color': '#262525', 'fontSize': '9px'}
    else:
        default_style = {'backgroundColor': 'white', 'border': '1px solid #eee', 'color': '#262525', 'fontSize': '14px'}
        active_style = {'backgroundColor': '#ddd', 'border': '1px solid #eee', 'color': '#262525', 'fontSize': '14px'}
    
    if button_id == 'btn-a':
        return [active_style, default_style, default_style]
    elif button_id == 'btn-b':
        return [default_style, active_style, default_style]
    elif button_id == 'btn-c':
        return [default_style, default_style, active_style]
    else:
        return [default_style, active_style, default_style]
    
@app.callback(
    [Output('btn-cc', 'style'),
     Output('btn-bb', 'style'),
    Output('btn-aa', 'style')],
    [Input('btn-aa', 'n_clicks'),
     Input('btn-bb', 'n_clicks'),
     Input('btn-cc', 'n_clicks'),
     Input('window-size-store', 'data')],
    prevent_initial_call=False
)
def update_button_style2(n1, n2, n3, window_size_data):
    width = window_size_data['width']
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if width <= 800:
        default_style = {'backgroundColor': 'white', 'border': '1px solid #eee', 'color': '#262525', 'fontSize': '9px'}
        active_style = {'backgroundColor': '#ddd', 'border': '1px solid #eee', 'color': '#262525', 'fontSize': '9px'}
    else:
        default_style = {'backgroundColor': 'white', 'border': '1px solid #eee', 'color': '#262525', 'fontSize': '14px'}
        active_style = {'backgroundColor': '#ddd', 'border': '1px solid #eee', 'color': '#262525', 'fontSize': '14px'}
    
    if button_id == 'btn-cc':
        return [active_style, default_style, default_style]
    elif button_id == 'btn-bb':
        return [default_style, active_style, default_style]
    elif button_id == 'btn-aa':
        return [default_style, default_style, active_style]
    else:
        print("-----------------------default")
        return [default_style, default_style, active_style]



if __name__ == '__main__':
    #app.run_server(debug=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
