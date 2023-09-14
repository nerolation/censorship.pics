import os
import dash
from dash import dcc
from dash import html
from datetime import datetime
from dash import dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import dash_bootstrap_components as dbc
import numpy as np
from dash import Input, Output
from plotly.subplots import make_subplots


QUERY = """
SELECT {}
FROM {}
{}
"""

def build_query(select, dataset, appendix=""):
    return QUERY.format(select, dataset, appendix)
BLACK = "rgb(15, 20, 25)"
BLACK_ALPHA = "rgba(15, 20, 25, {})"


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
        latest_data_validator
    )

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
        margin=dict(l=40, r=0, t=80, b=20),
        yaxis=dict(fixedrange =True),
        xaxis=dict(fixedrange =True),
        xaxis1=dict(showticklabels=False),  # Hide x-axis labels for first subplot
        xaxis2=dict(showticklabels=False),  # Hide x-axis labels for second subplot
        xaxis3=dict(showticklabels=False),  # Hide x-axis labels for third subplot
        yaxis1=dict(showticklabels=False),  # Hide y-axis labels for first subplot
        yaxis2=dict(showticklabels=False),  # Hide y-axis labels for second subplot
        yaxis3=dict(showticklabels=False),
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
                y0=1.1,
                y1=1.14-shape_delta_y,
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
                y0=1.02,
                y1=1.06-shape_delta_y,
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
        dict(label="Show Relays",
             method="update",
             args=[{"visible": [True for _ in range(fig1_len)] + [False for _ in range(fig2_len)] + [False for _ in range(fig3_len)]},
                   {"title": '<span style="font-size: 24px;font-weight:bold;">Censorship - Relays</span>'}]
            ),
        dict(label="Show Builders",
             method="update",
             args=[{"visible": [False for _ in range(fig1_len)] + [True for _ in range(fig2_len)] + [False for _ in range(fig3_len)]},
                   {"title": '<span style="font-size: 24px;font-weight:bold;">Censorship - Builders</span>'}]
            ),
        dict(label="Show Validators",
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
                showgrid=True, gridwidth=1, gridcolor=BLACK_ALPHA.format(0.2),tickfont=dict(size=font_size),
                
                
            type="date"
        ),
        yaxis=dict(
                showgrid=True, gridwidth=1, gridcolor=BLACK_ALPHA.format(0.2),tickfont=dict(size=font_size),
            title_font=dict(size=font_size+2), range=[0,100]
        ),  
    )


def create_censorship_over_last_month(df_censoring, df_relays_over_time, df_builders_over_time, df_validators_over_time):
    global fig1_len, fig2_len, fig3_len
    df_relays_over_time = df_relays_over_time[df_relays_over_time["timestamp"] > sorted(df_relays_over_time["timestamp"].unique())[-33]]
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


def fig1_layout(width=801):
    if width <= 800:
        font_size = 10
    else:
        font_size = 20
    return dict(
        title=f'<span style="font-size: {font_size}px;font-weight:bold;">Number of Missed Blocks Over Time</span>',
        xaxis_title='Date',
        yaxis_title='#Blocks',
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(family="Ubuntu Mono", size = font_size),
        hovermode = "x unified",
        hoverlabel=dict(
            font_size=font_size,
            font_family="Ubuntu Mono"
        ),
        legend=dict(
            x=0,           # x position of the legend (1 corresponds to the right end of the plot)
            y=1,           # y position of the legend (1 corresponds to the top of the plot)
            xanchor="auto",  # x anchor of the legend
            yanchor="auto",  # y anchor of the legend
            bgcolor="rgba(255, 255, 255, 0.7)" # You can set a background color for readability if needed
        ),
        xaxis=dict(
            fixedrange=True, 
            showgrid=True,
            gridcolor="#ffffff"   ,     
            gridwidth=1.5   ,     
        ),
        yaxis=dict(
            fixedrange=True, 
            showgrid=True,
            gridcolor="#ffffff",
            gridwidth=1.5,
        ),
        updatemenus=[dict(
            type="buttons",
            buttons=[
                dict(args=[{"visible": [True if i%2==0 else False for i in range(10)]},
                           {}],
                    label="Absolute",
                    method="update"
                )
                ,
                dict(args=[{"visible": [True if i%2==1 else False for i in range(10)]},
                               {}],
                        label="Relative",
                        method="update"
                )
                ],
            showactive= True,
            direction= 'left',
            active= 0,
            x= 1.0, 
            xanchor= 'right', 
            y= 1.15, 
            yanchor= 'top'
        )]
    )




# Figures
def create_figures(
    df_censorship, 
    df_relays_over_time, 
    df_builders_over_time, 
    df_validators_over_time,
    latest_data_relay, 
    latest_data_builder, 
    latest_data_validator
):
    fig_bars = censorship_bars(latest_data_relay, latest_data_builder, latest_data_validator)
    fig_over_months = create_censorship_over_last_month(df_censorship, df_relays_over_time, df_builders_over_time, df_validators_over_time)
    return fig_bars, fig_over_months

(df_censorship, df_relays_over_time, df_builders_over_time, df_validators_over_time,
 latest_data_relay, latest_data_builder, latest_data_validator) = prepare_data()
fig_bars, fig_over_months = create_figures(df_censorship, df_relays_over_time, df_builders_over_time, df_validators_over_time,
                                latest_data_relay, latest_data_builder, latest_data_validator)

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
        {'if': {'column_id': 'Slot Nr. in Epoch'}, 'maxWidth': '30px', 'text-align': 'center', 'fontSize': font_size},
        {'if': {'column_id': 'Slot'}, 'textAlign': 'right', 'maxWidth': '40px', 'fontSize': font_size},
        {'if': {'column_id': 'Parent Slot'}, 'textAlign': 'center', 'maxWidth': '40px', 'fontSize': font_size},
        {'if': {'column_id': 'Val. ID'}, 'maxWidth': '30px', 'fontSize': font_size},
        {'if': {'column_id': 'Date'}, 'maxWidth': '80px', 'fontSize': font_size},
        {'if': {'column_id': 'CL Client'}, 'maxWidth': '80px', 'fontSize': font_size}
    ]

@app.callback(
    Output('main-div', 'style'),
    Input('window-size-store', 'data')
)
def update_main_div_style(window_size_data):
    if window_size_data is None:
        raise dash.exceptions.PreventUpdate

    window_width = window_size_data['width']
    if window_width > 800:
        return {'margin-right': '110px', 'margin-left': '110px'}
    else:
        return {}

app.layout = html.Div(
    [
        dbc.Container(
        [
            # Title
            dbc.Row(html.H1("Ethereum Censorship Dashboard", style={'text-align': 'center','margin-top': '20px'}), className="mb-4"),
            html.Div([
                dbc.Row([
                    dbc.Col(
                        html.H5(
                            ['Built with 🖤 by ', html.A('Toni Wahrstätter', href='https://twitter.com/nero_eth', target='_blank')],
                            className="mb-4 even-smaller-text" # Apply the class
                        ),
                        width={"size": 6, "order": 1}
                    ),
                    dbc.Col(
                        html.H5(
                            ['Check out ', html.A('tornado-warning.info', href='https://tornado-warning.info', target='_blank'), " for more stats"],
                            className="mb-4 even-smaller-text text-right",
                            style={'textAlign': 'right', "margin-right": "2vw"}
                        ),
                        width={"size": 6, "order": 2}
                    )
                ])
            ]),
            #dbc.Row(
            #   html.H5(
            #            ['Reorg Overview', ' (last 30 days)'],
            #            className="mb-4 smaller-text" # Apply the class
            #        )
            #),
            #dbc.Row(
            #    dbc.Col(
            #        dash_table.DataTable(
            #            style_cell_conditional=table_styles(799),
            #            id='table',
            #            columns=[
            #                {"name": i, 
            #                 "id": i, 
            #                 'presentation': 'markdown'} if i == 'Slot' else {"name": i, "id": i} for i in df_table.columns#[:-1]
            #            ],# + [{"name": 'slot_sort', "id": 'slot_sort', "hidden": True}],
            #            data=df_table.to_dict('records'),
            #            page_size=15,
            #            style_table={'overflowX': 'auto'},
            #            style_cell={'whiteSpace': 'normal','height': 'auto'},
            #            style_data_conditional=[
            #                {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'},
            #            ],
            #            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            #            style_header_conditional=[
            #                {'if': {'column_id': 'Slot'}, 'text-align': 'center'},
            #                {'if': {'column_id': 'Parent Slot'}, 'text-align': 'center'},
            #                {'if': {'column_id': 'Slot Nr. in Epoch'}, 'text-align': 'center'},
            #            ],
            #            css=[dict(selector="p", rule="margin: 0; text-align: center")],
            #            sort_action="native",
            #            sort_mode="single"
            #        ),
            #        className="mb-4", md=12
            #    )
            #),

            # Graphs
            dbc.Row(dbc.Col(dcc.Graph(id='graph1', figure=fig_bars), md=12, className="mb-4")),
            dbc.Row(dbc.Col(dcc.Graph(id='graph2', figure=fig_over_months), md=12, className="mb-4")),


            dbc.Row(dcc.Interval(id='window-size-trigger', interval=1000, n_intervals=0, max_intervals=1)),
            dcc.Store(id='window-size-store',data={'width': 800})
        ],
        fluid=True,
    )],
    id='main-div'  # This ID is used in the callback to update the style
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


#
#@app.callback(
#    Output('graph3', 'figure'),
#    Input('window-size-store', 'data')
#)
#def update_layout3(window_size_data):
#    if window_size_data is None:
#        raise dash.exceptions.PreventUpdate
#    width = window_size_data['width']
#    fig3.update_layout(**fig3_layout(width))
#    return fig3
#
#@app.callback(
#    Output('graph4', 'figure'),
#    Input('window-size-store', 'data')
#)
#def update_layout4(window_size_data):
#    if window_size_data is None:
#        raise dash.exceptions.PreventUpdate
#    width = window_size_data['width']
#    fig4.update_layout(**fig4_layout(width))
#    return fig4
#
#@app.callback(
#    Output('graph5', 'figure'),
#    Input('window-size-store', 'data')
#)
#def update_layout5(window_size_data):
#    if window_size_data is None:
#        raise dash.exceptions.PreventUpdate
#    width = window_size_data['width']
#    fig5.update_layout(**fig5_layout(width))
#    return fig5
#
#@app.callback(
#    Output('graph6', 'figure'),
#    Input('window-size-store', 'data')
#)
#def update_layout6(window_size_data):
#    if window_size_data is None:
#        raise dash.exceptions.PreventUpdate
#    width = window_size_data['width']
#    fig6.update_layout(**fig6_layout(width))
#    return fig6
#@app.callback(
#    Output('graph7', 'figure'),
#    Input('window-size-store', 'data')
#)
#def update_layout7(window_size_data):
#    if window_size_data is None:
#        raise dash.exceptions.PreventUpdate
#    width = window_size_data['width']
#    fig7.update_layout(**fig7_layout(width))
#    return fig7
#
#@app.callback(
#    Output('graph8', 'figure'),
#    Input('window-size-store', 'data')
#)
#def update_layout8(window_size_data):
#    if window_size_data is None:
#        raise dash.exceptions.PreventUpdate
#    width = window_size_data['width']
#    fig8.update_layout(**create_reorger_relay_layout(width))
#    return fig8
#
#@app.callback(
#    Output('graph9', 'figure'),
#    Input('window-size-store', 'data')
#)
#def update_layout9(window_size_data):
#    if window_size_data is None:
#        raise dash.exceptions.PreventUpdate
#    width = window_size_data['width']
#    fig9.update_layout(**create_reorger_validator_layout(width))
#    return fig9
#
#@app.callback(
#    Output('graph10', 'figure'),
#    Input('window-size-store', 'data')
#)
#def update_layout10(window_size_data):
#    if window_size_data is None:
#        raise dash.exceptions.PreventUpdate
#    width = window_size_data['width']
#    fig10.update_layout(**create_reorger_builder_layout(width))
#    return fig10

if __name__ == '__main__':
    #app.run_server(debug=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
