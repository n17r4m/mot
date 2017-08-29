from __future__ import absolute_import

from numbers import Number

from plotly import exceptions, optional_imports
from plotly.figure_factory import utils
from plotly.graph_objs import graph_objs
from plotly.tools import make_subplots

pd = optional_imports.get_module('pandas')
np = optional_imports.get_module('numpy')
scipy_stats = optional_imports.get_module('scipy.stats')


def calc_stats(data):
    """
    Calculate statistics for use in violin plot.
    """
    x = np.asarray(data, np.float)
    vals_min = np.min(x)
    vals_max = np.max(x)
    q2 = np.percentile(x, 50, interpolation='linear')
    q1 = np.percentile(x, 25, interpolation='lower')
    q3 = np.percentile(x, 75, interpolation='higher')
    iqr = q3 - q1
    whisker_dist = 1.5 * iqr

    # in order to prevent drawing whiskers outside the interval
    # of data one defines the whisker positions as:
    d1 = np.min(x[x >= (q1 - whisker_dist)])
    d2 = np.max(x[x <= (q3 + whisker_dist)])
    return {
        'min': vals_min,
        'max': vals_max,
        'q1': q1,
        'q2': q2,
        'q3': q3,
        'd1': d1,
        'd2': d2
    }


def make_half_violin(x, y, fillcolor='#1f77b4', linecolor='rgb(0, 0, 0)'):
    """
    Produces a sideways probability distribution fig violin plot.
    """
    text = ['(pdf(y), y)=(' + '{:0.2f}'.format(x[i]) +
            ', ' + '{:0.2f}'.format(y[i]) + ')'
            for i in range(len(x))]

    return graph_objs.Scatter(
        x=x,
        y=y,
        mode='lines',
        name='',
        text=text,
        fill='tozerox',
        fillcolor=fillcolor,
        line=graph_objs.Line(width=0.5, color=linecolor, shape='spline'),
        hoverinfo='text',
        opacity=0.5
    )

def make_non_outlier_interval(s, d1, d2):
    """
    Returns the scatterplot fig of most of a violin plot.
    """
    return graph_objs.Scatter(
        x=[s, s],
        y=[d1, d2],
        name='',
        mode='lines',
        line=graph_objs.Line(width=1.5,
                             color='rgb(0,0,0)')
    )


def make_quartiles(s, q1, q3):
    """
    Makes the upper and lower quartiles for a violin plot.
    """
    return graph_objs.Scatter(
        x=[s, s],
        y=[q1, q3],
        text=['lower-quartile: ' + '{:0.2f}'.format(q1),
              'upper-quartile: ' + '{:0.2f}'.format(q3)],
        mode='lines',
        line=graph_objs.Line(
            width=4,
            color='rgb(0,0,0)'
        ),
        hoverinfo='text'
    )

def make_diff(m1, m2):
    """
    Makes the difference of medians for a violin plot.
    """
    return graph_objs.Scatter(
        x=[0, 0],
        y=[m1, m2],
        text=['median 1: ' + '{:0.2f}'.format(m1),
              'median 2: ' + '{:0.2f}'.format(m2)],
        mode='lines',
        line=graph_objs.Line(
            width=2,
            color='rgb(0,0,0)'
        ),
        hoverinfo='text'
    )

def make_delta(m1, m2):
    """
    Formats the 'delta of medians' hovertext for a violin plot.
    """
    return graph_objs.Scatter(
        x=[0],
        y=[(m1 + m2) / 2.0],
        text=['delta: ' + '{:0.2f}'.format(abs(m1 - m2))],
        mode='markers',
        marker=dict(symbol='square',
                    color='rgb(255,255,255)'),
        hoverinfo='text'
    )

def make_median(s, q2):
    """
    Formats the 'median' hovertext for a violin plot.
    """
    return graph_objs.Scatter(
        x=[s],
        y=[q2],
        text=['median: ' + '{:0.2f}'.format(q2)],
        mode='markers',
        marker=dict(symbol='square',
                    color='rgb(255,255,255)'),
        hoverinfo='text'
    )
    


def make_XAxis(xaxis_title, xaxis_range):
    """
    Makes the x-axis for a violin plot.
    """
    xaxis = graph_objs.XAxis(title=xaxis_title,
                             range=xaxis_range,
                             showgrid=False,
                             zeroline=False,
                             showline=False,
                             mirror=False,
                             ticks='',
                             showticklabels=False)
    return xaxis


def make_YAxis(yaxis_title):
    """
    Makes the y-axis for a violin plot.
    """
    yaxis = graph_objs.YAxis(title=yaxis_title,
                             showticklabels=True,
                             autorange=True,
                             ticklen=4,
                             showline=True,
                             zeroline=False,
                             showgrid=True,
                             mirror=False)
    return yaxis


def violinplot(vals, colors=None):
    """
    Refer to FigureFactory.create_violin() for docstring.
    """
    
    if colors is None:
        colors = ["#1F77B4", "#FF7F0E"]
    
    sides = [np.asarray(vals[0], np.float), np.asarray(vals[1], np.float)]
    
    #  summary statistics
    stats = [calc_stats(side) for side in sides]
    # kernel density estimation of pdf
    pdfs = [scipy_stats.gaussian_kde(side) for side in sides]
    # grid over the data interval
    xxs = [np.linspace(stat['min'], stat['max'], 100) for stat in stats]
    # evaluate the pdf at the grid xx
    yys = [pdf(xxs[i]) for i, pdf in enumerate(pdfs)]
    
    max_pdf = np.max([np.max(yy) for yy in yys])
    min_pdf = np.min([np.min(yy) for yy in yys])
    
    
    s_pos = max_pdf / 4.0
    
    # TODO consider min_pdf here
    plot_xrange = [min_pdf - 0.1, max_pdf + 0.1]
    
    plot_data = [make_half_violin(-yys[0], xxs[0], fillcolor=colors[0]),
                 make_half_violin(yys[1], xxs[1], fillcolor=colors[1]),
                 make_non_outlier_interval(-s_pos, stats[0]['d1'], stats[0]['d2']),
                 make_non_outlier_interval( s_pos, stats[1]['d1'], stats[1]['d2']),
                 make_quartiles(-s_pos, stats[0]['q1'], stats[0]['q3']),
                 make_quartiles( s_pos, stats[1]['q1'], stats[1]['q3']),
                 make_median(-s_pos, stats[0]['q2']),
                 make_median( s_pos, stats[1]['q2']),
                 make_diff(stats[0]['q2'], stats[1]['q2']),
                 make_delta(stats[0]['q2'], stats[1]['q2'])]
    
    return plot_data, plot_xrange
    
    


def violin2(data, labels, colors=None, height=450, width=600, title=None):
    """
    Split violin plot
    """
    
    if len(data) != len(labels):
         raise exceptions.PlotlyError("Data and Labels must be the same length")
    else:
        L = len(labels)

    fig = make_subplots(rows=1, cols=L,
                        shared_yaxes=True,
                        horizontal_spacing=0.025,
                        print_grid=False)
    color_index = 0
    for k, gr in enumerate(data):
        
        
        plot_data, plot_xrange = violinplot(gr, colors=colors)
        layout = graph_objs.Layout()

        for item in plot_data:
            fig.append_trace(item, 1, k + 1)
        
        # add violin plot labels
        fig['layout'].update(
            {'xaxis{}'.format(k + 1): make_XAxis(labels[k], plot_xrange)}
        )

    # set the sharey axis style
    fig['layout'].update({'yaxis{}'.format(1): make_YAxis('')})
    fig['layout'].update(
        title=title,
        showlegend=False,
        hovermode='closest',
        autosize=False,
        height=height,
        width=width
    )

    return fig
    
    
    
    
    