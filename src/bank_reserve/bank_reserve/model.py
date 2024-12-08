import mesa
from mesa.datacollection import DataCollector
from src.bank_reserve.bank_reserve.agents import Bank, Person


class BankReserves(mesa.Model):
    def __init__(self, init_people, rich_threshold, reserve_percent, interest_rate=0.05):
        # Modell inicializálása
        super().__init__()
        self.num_agents = init_people
        self.rich_threshold = rich_threshold
        self.reserve_percent = reserve_percent
        self.interest_rate = interest_rate  # Új kamatláb a felhasználó által állítható

        self.grid = mesa.space.MultiGrid(20, 20, True)
        self.schedule = mesa.time.RandomActivation(self)

        # Bank inicializálása
        self.bank = Bank(self.next_id(), self, reserve_percent=self.reserve_percent)

        # Ügynökök létrehozása
        for _ in range(self.num_agents):
            person = Person(
                self.next_id(),
                self,
                moore=True,
                bank=self.bank,
                rich_threshold=self.rich_threshold
            )
            self.schedule.add(person)

            # Véletlenszerű pozíció a rácson
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(person, (x, y))

        # Adatgyűjtő inicializálása
        self.datacollector = DataCollector(
            model_reporters={
                "Total Loans": lambda m: m.total_loans,  # Összes hitel a modellben
                "Total Savings": lambda m: sum(
                    a.savings for a in m.schedule.agents if isinstance(a, Person)
                ),  # Összes megtakarítás
                "Rich": lambda m: len(
                    [a for a in m.schedule.agents if isinstance(a, Person) and a.savings > m.rich_threshold]),
                "Middle": lambda m: len([a for a in m.schedule.agents if
                                         isinstance(a, Person) and a.savings <= m.rich_threshold and a.savings > 10]),
                "Poor": lambda m: len([a for a in m.schedule.agents if isinstance(a, Person) and a.savings <= 10])
            },
            agent_reporters={
                "Wealth": lambda a: a.wealth if isinstance(a, Person) else None,  # Ügynökök vagyona
                "Loans": lambda a: a.loans if isinstance(a, Person) else None,  # Ügynökök hitelei
            }
        )

        # Kezdeti állapot adatgyűjtés
        self.total_loans = 0
        self.datacollector.collect(self)

    def step(self):
        # Modell léptetése
        self.schedule.step()

        # Összesített hitel kiszámítása
        self.total_loans = sum(
            agent.loans for agent in self.schedule.agents if isinstance(agent, Person)
        )

        # Hitelkamat alkalmazása
        for agent in self.schedule.agents:
            if isinstance(agent, Person):
                # Hitelkamat hozzáadása a fennálló hitelekhez
                if agent.loans > 0:
                    interest = agent.loans * self.interest_rate
                    agent.loans += interest
                    self.bank.bank_loans += interest

        # Adatgyűjtés a gazdasági osztályok számához
        rich_count = 0
        middle_count = 0
        poor_count = 0

        for agent in self.schedule.agents:
            if isinstance(agent, Person):
                if agent.savings > self.rich_threshold:
                    rich_count += 1
                elif agent.savings < 10:
                    poor_count += 1
                else:
                    middle_count += 1

        # Adatgyűjtés
        self.datacollector.collect(self)
