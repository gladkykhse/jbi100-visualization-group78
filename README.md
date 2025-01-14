# JBI100 Visualization | Group 78

## Overview
This repository contains the source code for the **JBI100 Visualization** project by Group 78. The application provides insightful visualizations using modern tools and can be run locally using Docker.

The visualizations in this project are based on data from the [OSHA Establishment-Specific Injury and Illness Data](https://www.osha.gov/Establishment-Specific-Injury-and-Illness-Data).

## How to Launch the Application Locally

Follow these steps to set up and run the application:

1. Clone the repository:

   ```bash
   git clone git+https://github.com/gladkykhse/jbi100-visualization-group78.git
   ```

2. Navigate to the project directory:

   ```bash
   cd jbi100-visualization-group78
   ```

3. Build the Docker image:

   ```bash
   docker build -t dashboard-app .
   ```

4. Run the application:

   ```bash
   docker run -p 8080:8080 dashboard-app
   ```

5. Open your web browser and go to `http://localhost:8080` to access the application.

## Requirements
- Docker installed on your machine
- Internet connection to clone the repository

## Contributing
Feel free to submit issues or pull requests to contribute to this project.

## License
This project is licensed under the MIT License. See the LICENSE file for details.