# TrainNotificatorProject
project to create a daily notification go go and return to the office and keep updated about the trains taht i should take

functions ideas:

- Abfahrts: monitor that will read the departures in the time that im going to take the train, a few minutes before the desired time, will call the API and send via telegram to the user the status of the station, particullary the train that i should take. Informing about posible delay and info about the platform.
- night checker : every night will check the plan of the next train that i should take in the morning, to go and come back to the office. informing about possible "dissappearing" of the train or change of plans
- stations finder: send station name, and when possible type ( stop or station) and retrieves id of the desired station
- Create the schedules in main, to run in the moments that i want ( for now, when im waking up, and getting ready to leave the office, check the trains)
- prepare to deploy and run in docker ( requisites.txt )


HOW TO Setup
in order to set up the environment, run the next commands:
- python -m venv .venv
- source ./.venv/bin/activate
- pip install -r ./requierements.txt

Si no querés build en compose, el flujo manual queda así:

Build manual cuando quieras:
docker build -t bot-notificator:latest .

Levantar sin build:
docker compose up -d
Si cambias solo código Python (con volumen), normalmente alcanza con:
docker compose restart
Si cambias requirements:
docker build -t train-notificator:latest .
docker compose up -d