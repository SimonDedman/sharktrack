#!/usr/bin/env Rscript
# Plot BRUV stable recording duration and shark MaxN by station
#
# Usage:
#   Rscript plot_duration_maxn.R <durations_csv> <maxn_csv> [tracks_csv] [output_png]
#
#   durations_csv  - station-level durations (required)
#   maxn_csv       - shark MaxN per station (required)
#                    Accepts columns: coll/collection, stn/station_number,
#                    all/maxn_all, maxn_60min
#   tracks_csv     - shark track times (optional; omit or pass "" to skip)
#                    Expects columns: station_number, first_time
#   output_png     - output PNG path (optional; default: duration_maxn_by_station.png
#                    in same directory as durations_csv)
#
# Example:
#   Rscript plot_duration_maxn.R /tmp/station_level_durations.csv \
#     /tmp/maxn_shark_60min.csv /tmp/shark_track_times_per_station.csv \
#     ~/output/my_plot.png
#
# Design elements (DO NOT CHANGE without explicit user request):
# - Bars: geom_rect (not geom_col) with x-0.4 to x+0.4
# - Colours: Deployment=#E69F00, Stable=#56B4E9, Retrieval=#CC79A7
# - MaxN lines: All=#000000 (black), 60-min=#009E73 (dark green), linewidth=0.8
# - Track ticks: horizontal geom_segment (x-0.35 to x+0.35), grey30, linewidth=0.3
# - Y axis: 30-min graduations, no minor gridlines
# - 60-min reference: red dashed line
# - MaxN=0 stations: plotted as points on the baseline
# - Sorted by stable duration ascending

library(ggplot2)
library(dplyr)
library(tidyr)

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
  cat("Usage: Rscript plot_duration_maxn.R <durations_csv> <maxn_csv> [tracks_csv] [output_png]\n")
  cat("\n")
  cat("  durations_csv  Station-level durations CSV (required)\n")
  cat("  maxn_csv       Shark MaxN per station CSV (required)\n")
  cat("  tracks_csv     Shark track times CSV (optional, pass \"\" to skip)\n")
  cat("  output_png     Output PNG path (optional)\n")
  quit(status = 1)
}

durations_path <- args[1]
maxn_path <- args[2]
tracks_path <- if (length(args) >= 3 && nchar(args[3]) > 0) args[3] else NULL
output_path <- if (length(args) >= 4) {
  args[4]
} else {
  file.path(dirname(durations_path), "duration_maxn_by_station.png")
}

# --- Read and normalise column names ---

sdf <- read.csv(durations_path)

maxn <- read.csv(maxn_path)
# Normalise column names: accept coll/collection, stn/station_number, all/maxn_all
if ("coll" %in% names(maxn) && !"collection" %in% names(maxn)) {
  maxn <- maxn |> rename(collection = coll)
}
if ("stn" %in% names(maxn) && !"station_number" %in% names(maxn)) {
  maxn <- maxn |> rename(station_number = stn)
}
if ("all" %in% names(maxn) && !"maxn_all" %in% names(maxn)) {
  maxn <- maxn |> rename(maxn_all = all)
}

use_tracks <- FALSE
if (!is.null(tracks_path)) {
  if (file.exists(tracks_path)) {
    tracks <- read.csv(tracks_path) |>
      mutate(first_time_min = first_time / 60)
    use_tracks <- TRUE
  } else {
    cat("Warning: tracks file not found, skipping track ticks:", tracks_path, "\n")
  }
}

# --- Build plot data ---

plot_df <- sdf |>
  left_join(maxn, by = c("collection", "station_number")) |>
  mutate(
    station_label = sprintf("BRUV%02d", station_number),
    deploy_min = station_deploy_sec / 60,
    stable_min = station_stable_min,
    retrieve_min = station_retrieve_sec / 60,
    maxn_all = coalesce(maxn_all, 0L),
    maxn_60min = coalesce(maxn_60min, 0L)
  )

plot_df <- plot_df |>
  arrange(stable_min) |>
  mutate(
    station_label = factor(station_label, levels = station_label),
    x = as.numeric(station_label)
  )

rects <- plot_df |>
  mutate(
    stable_ymin = 0, stable_ymax = stable_min,
    retrieve_ymin = stable_min,
    retrieve_ymax = stable_min + retrieve_min,
    deploy_ymin = -deploy_min, deploy_ymax = 0
  )

rect_data <- bind_rows(
  rects |> transmute(x, component = "Stable", ymin = stable_ymin, ymax = stable_ymax),
  rects |> transmute(x, component = "Retrieval", ymin = retrieve_ymin, ymax = retrieve_ymax),
  rects |> transmute(x, component = "Deployment", ymin = deploy_ymin, ymax = deploy_ymax)
) |>
  filter(abs(ymax - ymin) > 0.01) |>
  mutate(component = factor(component,
    levels = c("Deployment", "Stable", "Retrieval")))

# --- Track ticks (optional) ---

if (use_tracks) {
  track_ticks <- tracks |>
    mutate(station_label = sprintf("BRUV%02d", station_number)) |>
    filter(station_label %in% plot_df$station_label) |>
    left_join(plot_df |> select(station_label, x, deploy_min), by = "station_label") |>
    mutate(tick_y = first_time_min - deploy_min)
}

# --- Secondary axis scaling ---

sec_max <- max(c(plot_df$maxn_all, plot_df$maxn_60min), na.rm = TRUE)
if (sec_max == 0) sec_max <- 1
max_pos <- max(plot_df$stable_min + plot_df$retrieve_min, na.rm = TRUE)
scale_factor <- max_pos / sec_max

line_data <- plot_df |>
  select(x, station_label, maxn_all, maxn_60min) |>
  pivot_longer(c(maxn_all, maxn_60min),
    names_to = "line_type", values_to = "maxn") |>
  mutate(
    maxn_scaled = maxn * scale_factor,
    line_type = factor(line_type,
      levels = c("maxn_all", "maxn_60min"),
      labels = c("MaxN (all)", "MaxN (60 min)"))
  )

bar_cols <- c("Deployment" = "#E69F00",
              "Stable" = "#56B4E9", "Retrieval" = "#CC79A7")
line_cols <- c("MaxN (all)" = "#000000", "MaxN (60 min)" = "#009E73")

min_neg <- min(-plot_df$deploy_min, na.rm = TRUE)
y_breaks <- seq(floor(min_neg / 30) * 30, ceiling(max_pos / 30) * 30, by = 30)

# --- Build plot ---

p <- ggplot() +
  geom_hline(yintercept = 0, colour = "grey40", linewidth = 0.4) +
  geom_rect(data = rect_data,
    aes(xmin = x - 0.4, xmax = x + 0.4, ymin = ymin, ymax = ymax, fill = component))

if (use_tracks) {
  p <- p +
    geom_segment(data = track_ticks,
      aes(x = x - 0.35, xend = x + 0.35, y = tick_y, yend = tick_y),
      colour = "grey30", linewidth = 0.3, alpha = 0.6)
}

p <- p +
  geom_line(data = line_data,
    aes(x = x, y = maxn_scaled, colour = line_type, group = line_type), linewidth = 0.8) +
  geom_point(data = line_data,
    aes(x = x, y = maxn_scaled, colour = line_type), size = 1.5) +
  geom_hline(yintercept = 60, colour = "red", linewidth = 0.5, linetype = "dashed") +
  scale_fill_manual(values = bar_cols, name = NULL) +
  scale_colour_manual(values = line_cols, name = NULL) +
  scale_x_continuous(breaks = plot_df$x, labels = plot_df$station_label, expand = c(0.01, 0.01)) +
  scale_y_continuous(
    name = "Duration (minutes)",
    breaks = y_breaks,
    minor_breaks = NULL,
    sec.axis = sec_axis(~ . / scale_factor, name = "Shark MaxN",
                        breaks = seq(0, sec_max + 2, by = 1))
  ) +
  labs(x = NULL, title = "BRUV Duration and Shark MaxN by Station") +
  theme_minimal(base_size = 10) +
  theme(
    axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5, size = 6),
    legend.position = "bottom",
    legend.box = "horizontal",
    legend.text = element_text(size = 8),
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    plot.title = element_text(size = 12, face = "bold")
  ) +
  guides(fill = guide_legend(order = 1, nrow = 1), colour = guide_legend(order = 2, nrow = 1))

# --- Save ---

dir.create(dirname(output_path), showWarnings = FALSE, recursive = TRUE)
ggsave(output_path, p, width = 18, height = 7, dpi = 200)
cat("Saved to:", output_path, "\n")
