# gamedata.py

class Disk:
    """条件（ディスク）を表すクラス"""
    def __init__(self, name, trigger, mana_gen, description, trigger_attribute=None):
        self.name, self.trigger, self.mana_gen = name, trigger, mana_gen
        self.description, self.trigger_attribute = description, trigger_attribute

class Spell:
    """魔法（スペル）を表すクラス"""
    def __init__(self, name, attribute, mana_cost, effect, value, description):
        self.attribute = attribute if isinstance(attribute, list) else [attribute]
        self.name, self.mana_cost = name, mana_cost
        self.effect, self.value, self.description = effect, value, description

class Relic:
    """遺物（レリック）を表すクラス"""
    def __init__(self, name, effect_type, value, description):
        self.name, self.effect_type, self.value = name, effect_type, value
        self.description = description

ALL_RELICS = [
    # ステータス強化
    Relic("生命の石", "increase_max_hp", 50, "最大HPが50増加する"),
    Relic("魔力の器", "increase_max_mana", 20, "全スロットの最大Manaが20増加する"),
    Relic("鋭利なレンズ", "increase_crit_chance", 0.10, "クリティカル率が10%増加する"),
    Relic("破壊の槌", "increase_crit_damage", 0.5, "クリティカルダメージが50%増加する"),
    Relic("幸運のコイン", "increase_stone_gain", 0.2, "戦闘で得られる魔石が20%増加する"),
    # 属性関連
    Relic("融和の書物", "integrate_attribute", ["火", "水"], "[火]と[水]属性を統合する"),
    Relic("嵐のトーテム", "integrate_attribute", ["雷", "土"], "[雷]と[土]属性を統合する"),
    Relic("燃え盛る残り火", "start_turn_buildup", {"attribute": "火", "amount": 10}, "ターン開始時、敵全体に[火]属性値を10与える"),
    Relic("凍てつく宝珠", "start_turn_buildup", {"attribute": "水", "amount": 10}, "ターン開始時、敵全体に[水]属性値を10与える"),
    # 属性解放バフ
    Relic("力の紋章", "buff_on_release", {"type": "attack", "value": 20, "duration": 3}, "属性解放時、3ターンの間、攻撃力が20増加する"),
    Relic("守りの紋章", "buff_on_release", {"type": "defense", "value": 15, "duration": 3}, "属性解放時、3ターンの間、防御力が15増加する"),
    Relic("会心の紋章", "buff_on_release", {"type": "crit_chance", "value": 0.2, "duration": 3}, "属性解放時、3ターンの間、クリティカル率が20%上昇する"),
    # 特殊効果
    Relic("生命の泉", "start_turn_heal", 5, "ターン開始時、HPが5回復する"),
    Relic("賢者の石", "overheal_to_mana", 0.5, "HP回復時、最大HPを超えた分の50%を全スロットのManaに変換する"),
    Relic("万物のプリズム", "integrate_attribute_all", [], "全ての属性を統合する（超希少）"),
]


ALL_DISKS = [
    # (v13から変更なし)
    Disk("反撃のディスク", "on_damage", 15, "ダメージを受けた時、Manaを15生成"),
    Disk("連鎖のディスク", "on_spell_cast", 7, "スペル発動時、Manaを7生成"),
    Disk("熟練のディスク", "on_spell_cast", 5, "スペル発動時、Manaを5生成"),
    Disk("追撃のディスク", "on_hit", 8, "スペルヒット時、Manaを8生成"),
    Disk("追撃のディスク・火", "on_hit", 16, "[火] スペルヒット時、Manaを16生成", '火'),
    Disk("追撃のディスク・水", "on_hit", 16, "[水] スペルヒット時、Manaを16生成", '水'),
    Disk("追撃のディスク・雷", "on_hit", 16, "[雷] スペルヒット時、Manaを16生成", '雷'),
    Disk("追撃のディスク・土", "on_hit", 16, "[土] スペルヒット時、Manaを16生成", '土'),
    Disk("魂刈りのディスク", "on_kill", 40, "敵を倒した時、Manaを40生成"),
    Disk("魂刈りのディスク・火", "on_kill", 55, "[火] 敵を倒した時、Manaを55生成", '火'),
    Disk("会心のディスク", "on_critical", 25, "クリティカル時、Manaを25生成"),
    Disk("会心のディスク・火", "on_critical", 30, "[火]クリティカル時、Manaを30生成", '火'),
    Disk("満タンのディスク", "on_mana_full", 20, "スロットのManaが満タンになった時、更にManaを20生成"),
    Disk("開幕のディスク", "combat_start", 50, "戦闘開始時、Manaを50得る"),
    Disk("決死のディスク", "on_low_hp", 30, "HPが30%以下になった時、Manaを30得る"),
    Disk("防壁のディスク", "on_defense_gain", 15, "防御を得た時、Manaを15生成"),
    Disk("共鳴のディスク", "on_elemental_release", 30, "属性が解放された時、Manaを30生成"),
    Disk("灼熱の共鳴", "on_elemental_release", 50, "[火] 属性が解放された時、Manaを50生成", '火'),
    Disk("深海の共鳴", "on_elemental_release", 50, "[水] 属性が解放された時、Manaを50生成", '水'),
    Disk("雷鳴の共鳴", "on_elemental_release", 50, "[雷] 属性が解放された時、Manaを50生成", '雷'),
    Disk("大地の共鳴", "on_elemental_release", 50, "[土] 属性が解放された時、Manaを50生成", '土'),
    Disk("強欲のディスク", "on_stone_gain", 1, "魔石1個得る毎に、Manaを1得る"),
]

ALL_SPELLS = [
    # (v14から変更なし)
    Spell("マジックミサイル", "無", 10, "damage", 15, "Mana10 / 15ダメージ"),
    Spell("パワーショット", "無", 30, "damage", 45, "Mana30 / 45ダメージ"),
    Spell("ヘイスト", "無", 35, "multi_damage", 3, "Mana35 / 15ダメージの3回攻撃"),
    Spell("ポイズン", "無", 25, "dot", 3, "[毒] Mana25 / 3ターンの間、毎ターン15ダメージ"),
    Spell("ウィークン", "無", 30, "debuff_attack", 10, "[弱体] Mana30 / 敵の攻撃力を永続で10下げる"),
    Spell("シールドブレイク", "無", 20, "damage_debuff_def", 20, "Mana20 / 20ダメージを与え、敵の防御を5下げる"),
    Spell("ファイアボール", "火", 20, "damage", 30, "[火] Mana20 / 30ダメージ"),
    Spell("インフェルノ", "火", 60, "damage", 100, "[火] Mana60 / 100ダメージ"),
    Spell("タイダルウェイブ", "水", 45, "damage", 60, "[水] Mana45 / 60ダメージ"),
    Spell("サンダーボルト", "雷", 30, "damage", 50, "[雷] Mana30 / 50ダメージ"),
    Spell("ライトニング", "雷", 40, "damage", 65, "[雷] Mana40 / 65ダメージ"),
    Spell("ウォール", "土", 20, "defense", 10, "[土] Mana20 / 次の被ダメージを10軽減"),
    Spell("アースクエイク", "土", 60, "damage", 100, "[土/全体] Mana60 / 敵全体に100ダメージ"),
    Spell("マナドレイン", "無", 15, "mana_drain", 20, "Mana15 / 20ダメージを与え、その半分を全スロットのManaに"),
    Spell("カオスボルト", "無", 40, "chaos", 0, "Mana40 / 何が起こるかわからない"),
    Spell("オーバーチャージ", "火", 30, "recoil_damage", 120, "[火] Mana30 / HP20消費、敵に120ダメージ"),
    Spell("リチュアル", "無", 0, "ritual", 60, "HP30消費、全スロットのManaを60得る"),
    Spell("プリズムウォール", "水", 50, "reflect", 1, "[水] Mana50 / 次の敵の攻撃を1回反射"),
    Spell("ブラッドラスト", "無", 20, "dynamic_damage", 1, "Mana20 / 失ったHP1あたり1ダメージ"),
    Spell("タイムワープ", "無", 90, "skip_turn", 1, "Mana90 / 敵の次のターンを1回スキップする"),
    Spell("死の指先", "無", 50, "execute", 0.2, "Mana50 / 敵のHPが20%以下なら即死させる"),
    Spell("ミラーイメージ", "無", 30, "big_defense", 999, "Mana30 / 次の被ダメージを1回だけ無効化する"),
    Spell("魔力供給", "無", 10, "mana_transfer", 10, "Mana10 / 他の全スロットのManaを10得る"),
    Spell("メテオ", ["火", "土"], 80, "damage", 70, "[火+土/全体] Mana80 / 敵全体に70ダメージ"),
    Spell("スチームブラスト", ["火", "水"], 40, "damage", 35, "[火+水] Mana40 / 35ダメージ"),
    Spell("プラズマボール", ["火", "雷"], 45, "damage", 40, "[火+雷] Mana45 / 40ダメージ"),
    Spell("サンドストーム", ["雷", "土"], 50, "damage", 45, "[雷+土/全体] Mana50 / 敵全体に45ダメージ"),
    Spell("プリズムスプレー", ["火", "水", "雷"], 70, "damage", 30, "[火+水+雷] Mana70 / 30ダメージ"),
    Spell("ボルテックス", ["水", "雷"], 60, "damage_debuff_def", 30, "[水+雷] Mana60 / 30ダメージを与え、敵の防御を永続で10下げる"),
    Spell("チェインライトニング", "雷", 35, "chain_damage", 40, "[雷] Mana35 / 敵に40ダメージ。残りの敵に半分のダメージ"),
]

