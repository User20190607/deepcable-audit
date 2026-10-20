"""Shared, declarative rules for cable-model parsing and normalization."""

# Longest-first matching is part of the parser contract.  Keep the source
# lists readable and expose sorted immutable tuples to consumers.
PREFIXES = tuple(sorted({
    'NH-ZC', 'NH-ZB', 'NH-ZA',
    'N-ZC', 'N-ZB', 'N-ZA', 'N-ZD', 'N-Z',
    'N-WDZC', 'N-WDZB', 'N-WDZA',
    'WDUZDNJ', 'WDUZDNS', 'WDUZDN',
    'WDUZCNJ', 'WDUZCNS', 'WDUZCN',
    'WDUZBNJ', 'WDUZBNS', 'WDUZBN',
    'WDUZANJ', 'WDUZANS', 'WDUZAN',
    'WDUZNJ', 'WDUZNS', 'WDUZN',
    'WDUZD', 'WDUZC', 'WDUZB', 'WDUZA', 'WDUZ',
    'WDZDNJ', 'WDZDNS', 'WDZDN',
    'WDZCNJ', 'WDZCNS', 'WDZCN',
    'WDZBNJ', 'WDZBNS', 'WDZBN',
    'WDZANJ', 'WDZANS', 'WDZAN',
    'WDZNJ', 'WDZNS', 'WDZN',
    'WDZD', 'WDZC', 'WDZB', 'WDZA', 'WDZ',
    'ZDNJ', 'ZDNS', 'ZDN',
    'ZCNJ', 'ZCNS', 'ZCN',
    'ZBNJ', 'ZBNS', 'ZBN',
    'ZANJ', 'ZANS', 'ZAN',
    'ZD', 'ZC', 'ZB', 'ZA', 'ZR', 'Z',
    'NJ', 'NS', 'N', 'NH',
}, key=len, reverse=True))

BASE_MODELS = tuple(sorted({
    'YJV22', 'YJV', 'YJY', 'KYJYP', 'KYJY', 'KVV', 'KVVP',
    'RYJSP', 'RYSP', 'RYJS', 'RYS', 'RVS', 'RVSP', 'RVVSP',
    'DJYPVRP', 'DJYVP',
    'BYJR', 'BYJ', 'BVR', 'BV',
    'RYJY', 'RYY', 'RVV', 'RVVP',
    'BBTRZ', 'RTTYZ', 'RTTVZ', 'RTTZ', 'RZDJ', 'RZDF',
    'BVV', 'VV', 'KYJP', 'RYJ',
}, key=len, reverse=True))

BASE_MODELS_SET = frozenset(BASE_MODELS)
SINGLE_CORE_WIRES = frozenset({'BYJ', 'BYJR', 'BVR', 'BV'})

# Defaults are applied only when an otherwise valid parsed model omits voltage.
DEFAULT_VOLTAGE = {
    'RYJSP': '300/300V', 'RYSP': '300/300V', 'RYJS': '300/300V',
    'RVS': '300/300V', 'RVSP': '300/300V', 'RVVSP': '300/300V',
    'KYJYP': '450/750V', 'KVVP': '450/750V', 'KVV': '450/750V',
    'KYJY': '450/750V', 'BYJR': '450/750V', 'BVR': '450/750V',
    'BYJ': '450/750V', 'BV': '450/750V', 'RZDJ': '450/750V',
    'RZDF': '450/750V',
    'RYJY': '300/500V', 'RYY': '300/500V', 'RVV': '300/500V',
    'RVVP': '300/300V', 'RYJYP': '300/300V', 'BVV': '300/500V',
    'DJYPVRP': '300/500V', 'DJYVP': '300/500V',
    'RTTZ': '0.6/1kV', 'RTTYZ': '0.6/1kV', 'RTTVZ': '0.6/1kV',
    'YJV22': '0.6/1kV', 'YJV': '0.6/1kV', 'YJY': '0.6/1kV',
    'VV': '0.6/1kV',
}
