"""Independent edge-case checks and saved-artifact contracts."""
from pathlib import Path
import importlib.util
import json
import sys
import numpy as np
import pandas as pd
import joblib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from common import native, ALL_FEATURES
from validation import numeric_tokens, allowed_numbers
from importlib import import_module
from pytest import raises

spec=importlib.util.spec_from_file_location('clean',ROOT/'src/01_clean_and_net.py')
clean=importlib.util.module_from_spec(spec)
spec.loader.exec_module(clean)
segments=import_module('05_segments')

def line(customer,stock,date,qty,price,invoice,row):
    return dict(CustomerID=customer,StockCode=stock,InvoiceDate=pd.Timestamp(date),Quantity=qty,Price=price,Invoice=invoice,source_row=row)

def test_chronology_lifo_partial_price_and_unmatched():
    p=pd.DataFrame([line(1,'A','2011-01-01',5,2,'A',0),line(1,'A','2011-01-03',4,3,'B',1),line(1,'A','2011-01-07',10,4,'C',2),line(2,'A','2011-01-01',8,1,'D',3)])
    c=pd.DataFrame([line(1,'A','2011-01-02',-2,9,'C1',4),line(1,'A','2011-01-04',-5,9,'C2',5),line(1,'A','2011-01-06',-9,9,'C3',6),line(np.nan,'A','2011-01-08',-3,9,'C4',7)])
    net,c,all_lines=clean.net_cancellations(p,c)
    assert all_lines.Quantity.tolist()==[0,8,0,10]  # sorted by date, then original row
    assert c.reversed_units.tolist()==[2,5,2,0]
    assert c.matched_flag.tolist()==['matched','matched','partly matched','unmatched']
    assert net.Revenue.sum()==48
    assert net.loc[net.CustomerID==1,'Invoice'].tolist()==['C']

def test_equal_timestamp_is_not_prior_purchase():
    p=pd.DataFrame([line(1,'A','2011-01-01',2,3,'A',0)])
    c=pd.DataFrame([line(1,'A','2011-01-01',-2,3,'C1',1)])
    net,c,_=clean.net_cancellations(p,c)
    assert net.Quantity.sum()==2 and c.reversed_units.sum()==0

def test_name_contradiction_rejected():
    with raises(AssertionError):
        segments.validate_name('Loyal champions',dict(recency='high',frequency='low',monetary='low'))
    with raises(AssertionError):
        segments.validate_name('Dormant buyers',dict(recency='low',frequency='low',monetary='low'))

def test_native_json():
    assert json.loads(json.dumps(native({'a':np.int64(3),'b':np.array([1,2]),'c':np.bool_(True)})))=={'a':3,'b':[1,2],'c':True}

def test_numeric_audit_handles_punctuation_and_percentage_points():
    assert numeric_tokens('2011, 103,697, 44, and 8% (0.438).')=={'2011','103,697','44','8%','0.438'}
    assert '8%' in allowed_numbers({'report_weight':8})
    assert '999999999999' not in allowed_numbers({'report_weight':8})

def test_saved_model_and_feature_contract():
    R=json.loads((ROOT/'outputs/results.json').read_text(encoding='utf-8'))
    model=joblib.load(ROOT/'outputs/model/customer_segmentation.joblib')
    assert list(model.named_steps)==['log','scale','kmeans']
    assert R['features']['all']==ALL_FEATURES
    assert R['model']['features']==json.loads((ROOT/'outputs/model/feature_columns.json').read_text())
    x=pd.DataFrame([R['model_test']['inputs']])[R['model']['features']]
    assert str(int(model.predict(x)[0]))==R['model_test']['label']
    f=pd.read_parquet(ROOT/'data/customer_segments.parquet')
    assert np.allclose(f.AOV,f.Monetary/f.Frequency)
    assert (f.loc[f.Outlier,'Segment']=='Outlier-Wholesale').all()
    assert np.isclose(f.Monetary.sum(),R['netting']['net_revenue'])
    assert np.isclose(sum(s['revenue_share'] for s in R['segments'].values()),1)
    for s in R['segments'].values():
        segments.validate_name(s['name'],s['tags'])

def test_regression_and_known_reversals():
    R=json.loads((ROOT/'outputs/results.json').read_text())
    assert R['regression']==clean.EXPECTED
    p=pd.read_parquet(ROOT/'data/net_purchases.parquet')
    for customer,invoice in [(16446,'581483'),(12346,'541431')]:
        assert not ((p.CustomerID==customer)&(p.Invoice==invoice)).any()
