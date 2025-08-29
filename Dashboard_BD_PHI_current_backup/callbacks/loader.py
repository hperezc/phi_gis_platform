from dash.dependencies import Input, Output, State
from dash import callback_context
from app import app

@app.callback(
    Output('page-loader', 'style'),
    [Input('refresh-data', 'n_clicks')],
    [State('page-loader', 'style')]
)
def toggle_loader(n_clicks, current_style):
    if not callback_context.triggered:
        return {'display': 'none'}
    
    if n_clicks:
        return {'display': 'flex'}
    
    return {'display': 'none'} 