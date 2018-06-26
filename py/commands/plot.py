

from lib.Database import Database

from uuid import UUID

from plotly import tools, utils
from lib.plots.violin2 import violin2


import plotly.offline as py
import plotly.figure_factory as ff
import plotly.graph_objs as go
import json
import numpy as np
import pandas as pd

db = Database()


async def main(args):

    if len(args) == 0:
        return "Invalid query"
    else:
        return await plot_query(*args)


async def plot_query(query, *args):
    return to_json(await getattr(Plots, query)(*args))


def to_json(figure):
    return json.dumps(
        {"data": figure.get("data", []), "layout": figure.get("layout", {})},
        cls=utils.PlotlyJSONEncoder,
    )


async def flow_vs_intensity_data(experiment, intensity=130):
    return {
        "Dark": [
            row["flow"] async
            for row in db.query(
                """
            SELECT AVG(-(t2.location[1] - t1.location[1]) * p.area) as flow
            FROM Track t1, Track t2, Frame f1, Frame f2, Particle p
            WHERE intensity < $1
            AND p.particle = t1.particle AND p.particle = t2.particle
            AND t1.particle = t2.particle
            AND t1.frame = f1.frame AND t2.frame = f2.frame
            AND f1.number = f2.number - 1 
            AND p.experiment = $2
            AND f1.experiment = $2 AND f2.experiment = $2
            GROUP BY p.particle
        """,
                float(intensity),
                UUID(experiment),
            )
        ],
        "Light": [
            row["flow"] async
            for row in db.query(
                """
            SELECT AVG(-(t2.location[1] - t1.location[1]) * p.area) as flow
            FROM Track t1, Track t2, Frame f1, Frame f2, Particle p
            WHERE intensity > $1
            AND p.particle = t1.particle AND p.particle = t2.particle
            AND t1.particle = t2.particle
            AND t1.frame = f1.frame AND t2.frame = f2.frame
            AND f1.number = f2.number - 1 
            AND p.experiment = $2
            AND f1.experiment = $2 AND f2.experiment = $2
            GROUP BY p.particle
        """,
                float(intensity),
                UUID(experiment),
            )
        ],
    }


async def flow_vs_category_data(experiment, category):
    return [
        row["flow"] async
        for row in db.query(
            """
            SELECT AVG(-(t2.location[1] - t1.location[1]) * p.area) as flow
            FROM Track t1, Track t2, Frame f1, Frame f2, Particle p
            WHERE category = $1
            AND p.particle = t1.particle AND p.particle = t2.particle
            AND t1.particle = t2.particle
            AND t1.frame = f1.frame AND t2.frame = f2.frame
            AND f1.number = f2.number - 1 
            AND p.experiment = $2
            AND f1.experiment = $2 AND f2.experiment = $2
            GROUP BY p.particle
        """,
            category,
            UUID(experiment),
        )
    ]


async def particle_size_distribution_data(experiment, category):
    return [
        row["diameter"] async
        for row in db.query(
            """
            SELECT p.radius * 2.0 AS diameter
            FROM  Particle p
            WHERE category = $1
            AND p.experiment = $2
        """,
            category,
            UUID(experiment),
        )
    ]


async def compare_experiment_flow_data(experiment):
    data = []
    for category in range(2, 4):
        data.append(
            [
                row["flow"] async
                for row in db.query(
                    """
            SELECT AVG(-(t2.location[1] - t1.location[1]) * p.area) as flow 
            FROM Track t1, Track t2, Frame f1, Frame f2, PArticle p 
            WHERE category = $1
            AND p.particle = t1.particle AND p.particle = t2.particle
            AND t1.particle = t2.particle
            AND t1.frame = f1.frame AND t2.frame = f2.frame
            AND f1.number = f2.number - 1 
            AND p.experiment = $2
            AND f1.experiment = $2 AND f2.experiment = $2
            GROUP BY p.particle
        """,
                    category,
                    UUID(experiment),
                )
            ]
        )
    return data


async def lookup_experiment_name(experiment):
    async for row in db.query(
        """
        SELECT name FROM Experiment where experiment = $1
    """,
        UUID(experiment),
    ):
        return row["name"]


class Plots:

    async def flow_vs_intensity_histogram(experiment, intensity=130):
        data = []
        for label, flows in (
            await flow_vs_intensity_data(experiment, intensity)
        ).items():
            data.append(go.Histogram(name=label, opacity=0.66, x=flows))
        layout = go.Layout(barmode="overlay")
        return go.Figure(data=data, layout=layout)

    async def flow_vs_intensity_distribution(experiment, intensity=130):
        data = await flow_vs_intensity_data(experiment, intensity)
        return ff.create_distplot(
            list(data.values()), list(data.keys()), bin_size=50, show_rug=False
        )

    async def flow_vs_intensity_violin(experiment, intensity=130):
        data = await flow_vs_intensity_data(experiment, intensity)
        df_cat_expand = ["Dark"] * len(data["Dark"]) + ["Light"] * len(data["Light"])
        df_val_expand = data["Dark"] + data["Light"]

        df = pd.DataFrame(dict(Flow=df_val_expand, Category=df_cat_expand))
        return ff.create_violin(
            df, data_header="Flow", group_header="Category", title=None, rugplot=False
        )

    async def flow_vs_category_histogram(experiment):

        labels = ["Undefined", "Unknown", "Bitumen", "Sand", "Bubble"]
        data = []
        for category in range(5):
            data.append(
                go.Histogram(
                    name=labels[category],
                    opacity=0.66,
                    x=await flow_vs_category_data(experiment, category),
                )
            )

        layout = go.Layout(barmode="overlay")
        return go.Figure(data=data, layout=layout)

    async def flow_vs_category_distribution(experiment):

        _labels = ["Undefined", "Unknown", "Bitumen", "Sand", "Bubble"]
        _data = []

        for category in range(5):
            _data.append(await flow_vs_category_data(experiment, category))

        labels = []
        data = []
        for i, d in enumerate(_data):
            if len(d) > 0:
                labels.append(_labels[i])
                data.append(d)

        return ff.create_distplot(data, labels, bin_size=50, show_rug=False)

    async def flow_vs_category_violin(experiment):
        labels = ["Undefined", "Unknown", "Bitumen", "Sand", "Bubble"]
        data = []
        for category in range(5):
            data.append(await flow_vs_category_data(experiment, category))

        labels = (
            (["Undefined"] * len(data[0]))
            + (["Unknown"] * len(data[1]))
            + (["Bitumen"] * len(data[2]))
            + (["Sand"] * len(data[3]))
            + (["Bubble"] * len(data[4]))
        )
        df = pd.DataFrame(
            dict(Flow=data[0] + data[1] + data[2] + data[3] + data[4], Category=labels)
        )
        return ff.create_violin(
            df, data_header="Flow", group_header="Category", title=None, rugplot=False
        )

    async def particle_size_distribution(experiment):
        _labels = ["Undefined", "Unknown", "Bitumen", "Sand", "Bubble"]
        _data = []
        for category in range(5):
            _data.append(await particle_size_distribution_data(experiment, category))

        labels = []
        data = []

        for i, d in enumerate(_data):
            if len(d) > 0:
                labels.append(_labels[i])
                data.append(d)
        data = np.nan_to_num(data)
        fig = ff.create_distplot(data, labels, bin_size=20, show_rug=False)
        fig["layout"].update(legend=dict(orientation="h"))
        return fig

    async def particle_counts_over_time(experiment):
        pass

    async def compare_flow_vs_category_violin2(*experiments):
        # print("experiments", experiments)

        data = [
            await compare_experiment_flow_data(experiment) for experiment in experiments
        ]
        labels = [
            await lookup_experiment_name(experiment) for experiment in experiments
        ]

        # print("lengths", len(data), len(labels))

        return violin2(data, labels)

    async def compare_particle_size_distribution(*experiments):
        # print("experiments", experiments)

        # Todo: all categories; undefined for now
        category = 0
        _data = [
            await particle_size_distribution_data(experiment, category)
            for experiment in experiments
        ]
        _labels = [
            await lookup_experiment_name(experiment) for experiment in experiments
        ]

        labels = []
        data = []

        for i, d in enumerate(_data):
            if len(d) > 0:
                labels.append(_labels[i])
                d = np.nan_to_num(d)
                data.append(d)
        fig = ff.create_distplot(data, labels, bin_size=20, show_rug=False)

        fig["layout"].update(legend=dict(orientation="h"))
        return fig
