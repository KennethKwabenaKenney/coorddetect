---
title: "coorddetect: Robust XYZ Coordinate Detection and Spatial QA/QC Diagnostics for Messy/big Tabular Geospatial Data"
tags:
  - python
  - geomatics
  - lidar
  - surveying
  - GIS
  - data analysis
  - data quality
authors:
  - name: Kenneth Kwabena Kenney
    orcid: https://orcid.org/0009-0002-8917-9870
    affiliation: 1, 2
affiliations:
  - name: Department of Civil Engineering, Oregon State University, USA
    index: 1
  - name: Nevada Gold Mines, USA
    index: 2
date: 2026-01-10
bibliography: paper.bib
---

## Summary

Reliable identification of spatial coordinates in messy or very big tabular datasets is a recurring challenge in geomatics, surveying, mining and GIS workflows, particularly when data originate from heterogeneous software systems or field instruments. In practice, coordinate columns may be unlabeled, reordered, or stored as numeric-like strings, complicating automated processing and quality control.

`coorddetect` is an open-source Python library that automatically detects X, Y, and Z coordinate columns from messy CSV and Excel files using a robust statistical heuristic based on numeric spread and column ordering. The library preserves original detection logic without relying on column names and supports optional spatial diagnostics, including robust bounding box estimation, convex hull geometry, and point density metrics. Batch processing and a command-line interface enable scalable integration into surveying and GIS pipelines and data preparation workflows.

The software is designed for practical use in real-world geospatial datasets and supports reproducible, automated preprocessing across a wide range of applications, specifically in geospatial research pipelines.

## Statement of Need

Many existing geospatial processing tools assume standardized column naming conventions or fixed schemas, which are often violated in operational datasets. In mining, LiDAR, and surveying environments, coordinate data are frequently exported from proprietary software with inconsistent formatting, embedded delimiters, or undocumented column orderings. This creates manual overhead and increases the risk of processing errors. This becomes more tedious when dealing with multiple large tabular datasets with over 100 columns where knowledge about the X,Y,Z columns is required.

`coorddetect` addresses this gap by providing a lightweight, schema-agnostic solution for identifying spatial coordinates directly from numeric behavior. By combining robust detection with optional spatial QA/QC diagnostics, the library enables both automation and validation, supporting downstream analysis, visualization, and integration with geographic information systems. This gives a stress-free automated detect of the X,Y,Z columns and its datasets extraction within multiple large tabular datasets. 

## Functionality

The core functionality of `coorddetect` includes:
- Automatic detection of X, Y, and Z coordinate columns using variance and range-based heuristics.
- Robust numeric cleanup of object-type columns containing numeric-like values.
- Optional computation of spatial diagnostics, including robust bounding boxes, convex hull geometry (2D and 3D), and point density metrics.
- Batch processing of CSV and Excel files.
- A command-line interface for folder-level automation.

The library is implemented in Python and distributed via PyPI, with comprehensive documentation and usage examples.

## Availability

The source code is publicly available on GitHub and distributed under the MIT License. The library can be installed using standard Python packaging tools and is compatible with Python 3.9 and later.


