import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from rich.console import Console
from rich.panel import Panel

console = Console()

class FinePredictor:
    def __init__(self, data_path='data/fines.csv', model_path='data/fine_model.pkl'):
        self.data_path = data_path
        self.model_path = model_path
        self.model = None
        self.is_trained = False

    def load_and_train(self):
        """Loads historical data and trains a Random Forest model."""
        if not os.path.exists(self.data_path):
            console.print(f"[bold red]Error: Data file '{self.data_path}' not found.[/bold red]")
            return False

        try:
            df = pd.read_csv(self.data_path)
            
            # Feature Selection: Records + Revenue
            X = df[['records_exposed', 'revenue_millions']]
            y = df['fine_amount']

            # Senior Logic: Use Random Forest instead of Linear Regression
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model.fit(X, y)
            
            self.is_trained = True
            console.print(f"[green]Model trained on {len(df)} historical regulatory actions.[/green]")
            return True

        except Exception as e:
            console.print(f"[red]Training Failed: {e}[/red]")
            return False

    def predict(self, records, revenue):
        """
        Returns a dictionary with the estimated fine and a probable range.
        """
        if not self.is_trained:
            return None

        # 1. Base Prediction
        inputs = [[records, revenue]]
        prediction = self.model.predict(inputs)[0]

        # 2. Confidence Interval (The "Senior" Touch)
        tree_predictions = [tree.predict(inputs)[0] for tree in self.model.estimators_]
        
        low_estimate = np.percentile(tree_predictions, 25) # 25th percentile
        high_estimate = np.percentile(tree_predictions, 75) # 75th percentile

        return {
            "fine_est": prediction,
            "low": low_estimate,
            "high": high_estimate
        }

if __name__ == "__main__":
    console.clear()
    console.print(Panel.fit("[bold blue]Regulatory Fine Predictor (v3.0)[/bold blue]\n[dim]Powered by Random Forest Regression[/dim]"))

    predictor = FinePredictor()
    if predictor.load_and_train():
        print("-" * 50)
        try:
            # Interactive Input
            in_records = int(input("  Enter Records Exposed (e.g. 50000): "))
            in_revenue = int(input("  Enter Company Revenue ($M): "))

            result = predictor.predict(in_records, in_revenue)

            console.print("\n[bold]SCENARIO ANALYSIS:[/bold]")
            console.print(f"   Records Lost: [cyan]{in_records:,}[/cyan]")
            console.print(f"   Revenue:      [cyan]${in_revenue:,}M[/cyan]")
            
            console.print("\n[bold]LIABILITY FORECAST:[/bold]")
            console.print(f"   [dim]Optimistic Case:[/dim]  [green]${result['low']:,.2f}[/green]")
            console.print(f"   [bold]Likely Fine:[/bold]      [yellow]${result['fine_est']:,.2f}[/yellow]")
            console.print(f"   [dim]Worst Case:[/dim]     [red]${result['high']:,.2f}[/red]")
            
            console.print("\n[italic dim]Disclaimer: Based on historical data. Not legal advice.[/italic dim]")

        except ValueError:
            console.print("[red]Invalid input. Numbers only please.[/red]")
