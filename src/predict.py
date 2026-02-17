import pandas as pd
import numpy as np
import io
from sklearn.ensemble import RandomForestRegressor
from rich.console import Console
from rich.panel import Panel

console = Console()

# Embedded Training Data (Simplicity > Complexity)
TRAINING_DATA = """records_exposed,revenue_millions,fine_amount
500000,1500,1200000
15000,10,25000
8000000,12000,30000000
1000,5,15000
4000,15,40000
65000,80,600000
150000,2000,5500000
10000000,50000,250000000
2200,8,20000
5000,25,125000
300000,1200,800000
10000,50,100000
147000000,3400,575000000
339000000,20000,23000000
600000,150,1200000
500,2,5000
1500000,4000,15000000
125000,600,900000
9000000,2500,10000000
200000,500,1200000
79000000,78000,115000000
41000000,45000,35000000
100000,100,500000
55000,90,550000
1000000,300,1500000"""

class FinePredictor:
    def __init__(self):
        self.model = None
        self.is_trained = False

    def load_and_train(self):
        """Trains Random Forest on embedded data."""
        try:
            # Read from the string constant instead of a file
            df = pd.read_csv(io.StringIO(TRAINING_DATA))
            
            # Feature Selection
            X = df[['records_exposed', 'revenue_millions']]
            y = df['fine_amount']

            # Train Model
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model.fit(X, y)
            
            self.is_trained = True
            console.print(f"[green]Model trained on {len(df)} internal historical records.[/green]")
            return True

        except Exception as e:
            console.print(f"[red]Training Failed: {e}[/red]")
            return False

    def predict(self, records, revenue):
        if not self.is_trained:
            return None

        inputs = [[records, revenue]]
        prediction = self.model.predict(inputs)[0]

        # Calculate Confidence Interval
        tree_predictions = [tree.predict(inputs)[0] for tree in self.model.estimators_]
        low_estimate = np.percentile(tree_predictions, 25)
        high_estimate = np.percentile(tree_predictions, 75)

        return {
            "fine_est": prediction,
            "low": low_estimate,
            "high": high_estimate
        }

if __name__ == "__main__":
    console.clear()
    console.print(Panel.fit("[bold blue]Regulatory Fine Predictor (v3.1)[/bold blue]\n[dim]Standalone Edition[/dim]"))

    predictor = FinePredictor()
    if predictor.load_and_train():
        print("-" * 50)
        try:
            in_records = int(input("  Enter Records Exposed (e.g. 50000): "))
            in_revenue = int(input("  Enter Company Revenue ($M): "))

            result = predictor.predict(in_records, in_revenue)

            console.print("\n[bold]LIABILITY FORECAST:[/bold]")
            console.print(f"   [dim]Optimistic Case:[/dim]  [green]${result['low']:,.2f}[/green]")
            console.print(f"   [bold]Likely Fine:[/bold]      [yellow]${result['fine_est']:,.2f}[/yellow]")
            console.print(f"   [dim]Worst Case:[/dim]     [red]${result['high']:,.2f}[/red]")

        except ValueError:
            console.print("[red]Invalid input. Numbers only please.[/red]")
