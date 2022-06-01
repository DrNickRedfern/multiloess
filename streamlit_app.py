
import streamlit as st
import io
import numpy as np
import pandas as pd
import seaborn as sns
from statsmodels.nonparametric.smoothers_lowess import lowess
from matplotlib import cm, colors
from matplotlib import pyplot as plt

st.title("Visualise movie editing data")

st.markdown("""
This app fits multiple loess smoothers to visualise motion picture shot length data.

LOESS, or [locally estimated scatterplot smoothing](https://en.wikipedia.org/wiki/Local_regression), is a nonparametric method for fitting a curve to an independent variable. Rather than fitting a global model, LOESS fits a function to a localised section of the data. The size of the segment of the data used to fit a curve is determined by the span of the local window, with more data used in fitting the curve as the span increases.

This app allows the analyst to identify the editing structure of a film at different scales by using different spans without committing the analyst to a particular level of smoothing before applying the function. At the macro-scale, LOESS smoothers with large spans describe the dominant trend in the editing of a film; while at the micro-scale smoothers with small spans reveal transient features associated with the editing of specific moments in a film.

The resulting plot can be used diagnostically for exploratory data analysis in order to decide which spans for the LOESS smoother are the most informative or for limiting the range of spans used for cross-validation to speed up the process of selecting the best span to describe the data.

## How to use this app
This app is easy to use.

* Upload a `.csv` file and select the column of data you want to visualise. The data should be in wide format, with one column per film. `NA` values are automatically removed.
* Select the range of spans you want to visualise by setting the `Low` and `High` parameters.
* Set the `Step` increase for the loess smoothers across the range.
* Set the distance between tick marks on the colour bar in the legend by setting a value for `Ticks`. The range of the colour bar is inherited from `Low` and `High`.
* Enter a title for the plot (usually this wll be the title of the film).
* Click the `Visualise` button to plot the data.

You can download the plot of your data by clicking on the `Download my plot` button.

### Access the code
You can find the code used to visualise the data on my GitHub repository for [multiple loess smoothers](https://github.com/DrNickRedfern/multiloesssmoothers).
""")

st.sidebar.header('Set the parameters for your plot')
st.sidebar.subheader("Upload your data")
uploaded_file = st.sidebar.file_uploader(
    "Data should be stored in wide format in a csv file", type=['csv'], accept_multiple_files=False)

# Declare film as an empty string before it is needed to suppress warnings about undefined variables.
film = ""

if uploaded_file is not None:
    file_details = {"File name": uploaded_file.name,
                    "File type": uploaded_file.type, "File size": uploaded_file.size}

    st.subheader("Your Data")
    st.write(file_details)
    df = pd.read_csv(uploaded_file)
    st.dataframe(df.round(1))

    st.sidebar.subheader("Select your data")
    film = st.sidebar.selectbox("Choose a film", list(df.columns.values))
    index = df.columns.get_loc(film)
    film_data = df.iloc[:, index].dropna(axis=0, how='any')

st.sidebar.subheader("Set the range")
loess_range = st.sidebar.slider(
    'Select a range of loess smoothers', min_value=0.1, max_value=0.9, value=(0.1, 0.9))
st.sidebar.subheader("Step")
loess_step = st.sidebar.slider(
    "Select the step between loess smoothers", min_value=0.01, max_value=0.25, value=0.1)
st.sidebar.subheader("Ticks")
ticks = st.sidebar.slider("Set the colour bar ticks",
                          min_value=0.01, max_value=0.25, value=0.1)
st.sidebar.subheader("Title")
plot_title = st.sidebar.text_input("Enter a title for the plot", value="")

st.sidebar.subheader("Click Visualise when you're ready to go")
if st.sidebar.button("Visualise"):

    times = np.cumsum(film_data)
    times = 100 * (times/np.max(times))

    spans = np.round(
        np.arange(loess_range[0], loess_range[1]+loess_step, loess_step).tolist(), 2)

    # Collect the results of fitting multiple smoothers
    column_names = ["span", "times", "fit"]
    dat_out = pd.DataFrame(columns=column_names)

    for s in spans:
        fit = pd.Series(
            lowess(film_data, times, is_sorted=True, frac=s, it=1)[:, 1])
        span = pd.Series(np.repeat(s, len(times)))
        dat_res = pd.DataFrame({"span": span, "times": times, "fit": fit})
        dfs = [dat_out, dat_res]
        dat_out = pd.concat(dfs, ignore_index=True)

    # Create the plot
    sns.set_theme(style="whitegrid")
    fig = sns.relplot(data=dat_out, x="times", y="fit", hue="span",
                      kind="line", palette="viridis", legend=False, height=6, aspect=1.3)
    fig.set(xlabel="Running time (%)", ylabel="Fitted values (s)")
    plt.title(plot_title, fontsize=14, weight='bold')
    plt.colorbar(cm.ScalarMappable(norm=colors.Normalize(vmin=dat_out['span'].min(), vmax=dat_out['span'].max(), clip=False), cmap='viridis'), ticks=np.arange(
        loess_range[0], loess_range[1]+loess_step, ticks), label=r'Span', orientation='horizontal', shrink=0.8, aspect=20, pad=0.15)

    st.subheader("Your plot")
    st.pyplot(fig, clear_figure=False)

# streamlit has no limit on the scope of an action. This means that clicking on the download button will re-run the entire app (https://github.com/streamlit/streamlit/issues/3832), causing the plot to disappear when it is saved. Keep an eye out for a solution to this problem that doesn't rely on session states, which don't seem to work.
download_file = film + ".png"
img = io.BytesIO()
plt.savefig(img, format='png', dpi=300, bbox_inches='tight')

st.sidebar.subheader("Save your plot as a .png file")
st.sidebar.download_button(
    "Download my plot", data=img, file_name=download_file, mime="image/png")
