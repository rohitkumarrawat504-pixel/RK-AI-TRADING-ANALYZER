from app.paper_trading import DemoPaperTrading


def test_demo_paper_trading():
    account = DemoPaperTrading(starting_balance=10000)
    account.open_position("BTC-USD", "BUY", 0.5, 100)
    trade = account.close_position("BTC-USD", 110)
    assert trade["demo"] is True
    assert account.get_summary()["demo_only"] is True
