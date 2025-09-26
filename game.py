# game.py
import random
import time
import os
from gamedata import ALL_DISKS, ALL_SPELLS, ALL_RELICS, Disk, Spell, Relic

# --- 定数 ---
GAME_TICK = 0.1
CORE_MANA_PER_SEC = 10
ELEMENTAL_THRESHOLD = 100
DISK_SELL_PRICE, SPELL_SELL_PRICE, RELIC_SELL_PRICE = 5, 5, 25

# --- クラス定義 ---
class Player:
    def __init__(self):
        self.base_max_hp, self.hp, self.max_hp = 100, 100, 100
        self.stones, self.max_slots = 40, 3
        self.core_slot = {"spell": None, "mana": 0}
        self.equipment = [{"disk": None, "spell": None, "mana": 0} for _ in range(self.max_slots)]
        self.relic_slots = [None] * self.max_slots
        self.owned_disks, self.owned_spells, self.owned_relics = [], [], []
        self.defense, self.base_crit_chance, self.crit_chance, self.crit_multiplier = 0, 0.15, 0.15, 1.5
        self.low_hp_triggered, self.reflect_turns = False, 0
        self.buffs = {}
        self.max_mana = 100
    def is_alive(self): return self.hp > 0
    def update_stats_by_relics(self):
        self.max_hp = self.base_max_hp + sum(r.value for r in self.relic_slots if r and r.effect_type == 'increase_max_hp')
        self.max_mana = 100 + sum(r.value for r in self.relic_slots if r and r.effect_type == 'increase_max_mana')
        self.crit_chance = self.base_crit_chance + sum(r.value for r in self.relic_slots if r and r.effect_type == 'increase_crit_chance')
        self.crit_multiplier = 1.5 + sum(r.value for r in self.relic_slots if r and r.effect_type == 'increase_crit_damage')
    def take_damage(self, amount, is_spell=False):
        hp_before = self.hp
        actual_damage = amount - self.defense if amount - self.defense > 0 else 0
        self.hp -= actual_damage; self.hp = max(0, self.hp)
        if not is_spell: print(f"プレイヤーは {actual_damage} のダメージ！ (残りHP: {self.hp}/{self.max_hp})")
        self.defense = 0
        if hp_before > self.max_hp*0.3 and self.hp <= self.max_hp*0.3 and not self.low_hp_triggered:
            self.low_hp_triggered = True; return True
        return False
    def heal(self, amount):
        overheal = max(0, self.hp + amount - self.max_hp)
        self.hp += amount; self.hp = min(self.max_hp, self.hp)
        print(f"プレイヤーはHPを {amount} 回復！ (現在HP: {self.hp}/{self.max_hp})")
        return overheal
    def add_stones(self, amount):
        stone_gain_bonus = 1.0 + sum(r.value for r in self.relic_slots if r and r.effect_type == 'increase_stone_gain')
        actual_gain = int(amount * stone_gain_bonus)
        self.stones += actual_gain
        return actual_gain

class Enemy:
    def __init__(self, name, hp, attack, defense, stone_reward, attack_interval=5.0):
        self.name, self.hp, self.attack, self.defense = name, hp, attack, defense
        self.max_hp, self.stone_reward = hp, stone_reward
        self.status_effects = {}; self.elemental_buildup = {"火": 0, "水": 0, "雷": 0, "土": 0}
        self.paralyzed_turns, self.skip_turns = 0, 0
        self.attack_interval = attack_interval
        self.attack_gauge = 0.0
    def is_alive(self): return self.hp > 0
    def take_damage(self, amount):
        actual_damage = amount - self.defense if amount - self.defense >= 1 else 1
        self.hp -= actual_damage; self.hp = max(0, self.hp)
        print(f"{self.name} に {actual_damage} のダメージ！ (残りHP: {self.hp})")
    def apply_timed_effects(self):
        if 'dot' in self.status_effects:
            self.take_damage(self.status_effects['dot']['value']); print(f"{self.name} は毒のダメージ！")
            self.status_effects['dot']['duration'] -= 1
            if self.status_effects['dot']['duration'] <= 0: del self.status_effects['dot']; print(f"{self.name} の毒が消えた。")
        if 'burn' in self.status_effects:
            self.take_damage(self.status_effects['burn']['value']); print(f"{self.name} は火傷のダメージ！")
            self.status_effects['burn']['duration'] -= 1
            if self.status_effects['burn']['duration'] <= 0: del self.status_effects['burn']; print(f"{self.name} の火傷が消えた。")

# --- ゲーム進行コアロジック ---
def apply_spell_effect(player, enemies, spell, slot_index_str):
    print(f"『{spell.name}』の効果！")
    attack_buff = player.buffs.get('attack', {}).get('value', 0)
    is_aoe = '土' in spell.attribute
    all_enemies = [e for e in enemies if e.is_alive()]
    primary_target = min(all_enemies, key=lambda x: x.hp, default=None)
    targets = all_enemies if is_aoe else ([primary_target] if primary_target else [])

    for i, enemy in enumerate(targets):
        enemy_was_alive, is_crit, damage_dealt = enemy.is_alive(), False, 0
        if spell.effect == "damage":
            damage = spell.value + attack_buff
            if random.random() < player.crit_chance: is_crit=True; damage=int(damage*player.crit_multiplier); print("クリティカル！")
            damage_dealt = damage; enemy.take_damage(damage)
        elif spell.effect == "chain_damage":
            damage = spell.value + attack_buff
            if random.random() < player.crit_chance: is_crit=True; damage=int(damage*player.crit_multiplier); print("クリティカル！")
            damage_dealt = damage; enemy.take_damage(damage)
            other_targets = [e for e in all_enemies if e is not enemy]
            for other in other_targets:
                print(f"稲妻が連鎖し、{other.name}に{int(damage/2)}ダメージ！")
                other.take_damage(int(damage/2))
        elif spell.effect == "dynamic_damage":
            damage = (player.max_hp - player.hp) * spell.value + attack_buff
            print(f"失われたHPが力に！ {damage}ダメージ！")
            damage_dealt = damage; enemy.take_damage(damage)
        elif spell.effect == "execute":
            if enemy.hp / enemy.max_hp <= spell.value:
                print(f"死の指先が{enemy.name}の命を刈り取った！")
                enemy.hp = 0
            else:
                print("しかし、敵は持ちこたえた！")
        if spell.attribute and '無' not in spell.attribute:
            for attr in spell.attribute:
                if attr in enemy.elemental_buildup:
                    buildup_amount = int(damage_dealt / 2) if damage_dealt > 0 else 10
                    enemy.elemental_buildup[attr] += buildup_amount
                    print(f"[{attr}]属性値が{buildup_amount}蓄積。(現在:{enemy.elemental_buildup[attr]})")
                    if enemy.elemental_buildup[attr] >= ELEMENTAL_THRESHOLD:
                        enemy.elemental_buildup[attr] -= ELEMENTAL_THRESHOLD; print(f"◇◆ {attr}属性解放！ ◆◇")
                        for relic in player.relic_slots:
                            if relic and relic.effect_type == 'buff_on_release':
                                buff = relic.value
                                player.buffs[buff['type']] = {'value': buff['value'], 'duration': buff['duration'] * 5}
                                print(f"遺物効果({relic.name}): {buff['duration']*5}秒間、{buff['type']}が{buff['value']}上昇！")
                        process_event(player, enemies, "on_elemental_release", attr)
                        if attr == '火': enemy.status_effects['burn'] = {'duration': 3, 'value': 30}; print(f"{enemy.name}は激しく燃え上がった！")
                        elif attr == '水': enemy.attack=max(1, enemy.attack-10); enemy.defense=max(0, enemy.defense-10); print(f"{enemy.name}が弱体化！")
                        elif attr == '雷': enemy.paralyzed_turns = 2; print(f"{enemy.name}は麻痺して動けない！")
                        elif attr == '土': print(f"大地が揺れ、敵全体に大ダメージ！"); [e.take_damage(150) for e in enemies if e.is_alive()]
                        time.sleep(0.5)
        if spell.effect.startswith("damage") or spell.effect in ["recoil_damage", "dynamic_damage"]:
            process_event(player, enemies, "on_hit", spell.attribute)
            if is_crit: process_event(player, enemies, "on_critical", spell.attribute)
            if enemy_was_alive and not enemy.is_alive(): process_event(player, enemies, "on_kill", spell.attribute)
    
    if spell.effect == "heal":
        overheal = player.heal(spell.value)
        if overheal > 0:
            for relic in player.relic_slots:
                if relic and relic.effect_type == 'overheal_to_mana':
                    mana_gain = int(overheal * relic.value)
                    print(f"遺物効果({relic.name}): 超過回復分がManaに変換！")
                    player.core_slot["mana"] = min(player.max_mana, player.core_slot["mana"] + mana_gain)
                    for s in player.equipment: s["mana"] = min(player.max_mana, s["mana"] + mana_gain)
    elif spell.effect == "big_defense": player.defense = 999; print("次の一撃を無効化するバリアを展開！")
    elif spell.effect == "skip_turn":
        if primary_target: primary_target.skip_turns += spell.value; print(f"{primary_target.name}の時を止め、行動を1回スキップ！")
    elif spell.effect == "mana_transfer":
        slot_index = -1
        if "スロット" in slot_index_str:
            try: slot_index = int(slot_index_str.split(' ')[-1]) - 1
            except (ValueError, IndexError): pass
        for i, s in enumerate(player.equipment):
            if i != slot_index : s["mana"] = min(player.max_mana, s["mana"] + spell.value)
        if slot_index_str != "コア":
             player.core_slot["mana"] = min(player.max_mana, player.core_slot["mana"] + spell.value)

    process_event(player, enemies, "on_spell_cast", spell.attribute)

def process_event(player, enemies, trigger_type, attribute_list):
    mana_generated = False
    attributes = attribute_list if isinstance(attribute_list, list) else [attribute_list]
    integration_relics = [r.value for r in player.relic_slots if r and r.effect_type == 'integrate_attribute']
    if any(r for r in player.relic_slots if r and r.effect_type == 'integrate_attribute_all'):
        integrated_attributes = {"火", "水", "雷", "土"}
    else:
        integrated_attributes = set(attributes)
        for group in integration_relics:
            if any(attr in group for attr in integrated_attributes):
                integrated_attributes.update(group)
    for i, slot in enumerate(player.equipment):
        disk = slot.get("disk")
        if disk and disk.trigger == trigger_type:
            if disk.trigger_attribute is None or disk.trigger_attribute in integrated_attributes:
                mana_before = slot["mana"]; print(f"スロット{i+1}のディスク効果: {disk.name}！")
                slot["mana"] = min(player.max_mana, slot["mana"] + disk.mana_gen)
                print(f"スロット{i+1}のManaを{disk.mana_gen}生成！ (現在: {slot['mana']})")
                if mana_before < player.max_mana and slot["mana"] == player.max_mana: process_event(player, enemies, "on_mana_full", None)
                mana_generated = True
    if mana_generated: cast_all_possible_spells(player, enemies)

def cast_all_possible_spells(player, enemies):
    while True:
        casted_in_loop = False
        core_spell = player.core_slot.get("spell")
        if core_spell and player.core_slot["mana"] >= core_spell.mana_cost:
            casted_in_loop = True; player.core_slot["mana"] -= core_spell.mana_cost
            print(f"\n>> [コア] {core_spell.name} 発動！(残りMana: {player.core_slot['mana']})")
            apply_spell_effect(player, enemies, core_spell, "コア")
        for i, slot in enumerate(player.equipment):
            spell = slot.get("spell")
            if spell and slot["mana"] >= spell.mana_cost:
                casted_in_loop = True; slot["mana"] -= spell.mana_cost
                print(f"\n>> [スロット{i+1}] {spell.name} 発動！(残りMana: {slot['mana']})")
                apply_spell_effect(player, enemies, spell, f"スロット {i+1}")
        if not casted_in_loop: break

# --- UI & ゲームフロー関数 ---
def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')
def get_gauge_bar(current, maximum):
    bar_length = 10
    if maximum == 0: return f"[{'-'*bar_length}]"
    filled_length = int(bar_length * current // maximum)
    return f"[{'|'*filled_length}{'-'*(bar_length-filled_length)}]"

def display_status(player, enemies):
    buff_str = " ".join([f"[{k.upper()}:{v['value']}({int(v['duration'])}s)]" for k, v in player.buffs.items()])
    print("---")
    print(f"【あなた】 HP: {player.hp}/{player.max_hp} {get_gauge_bar(player.hp, player.max_hp)} {buff_str}")
    core_spell_name = player.core_slot["spell"].name if player.core_slot["spell"] else "空"
    print(f"  コアスロット Mana: {int(player.core_slot['mana'])}/{player.max_mana} {get_gauge_bar(player.core_slot['mana'], player.max_mana)} ({core_spell_name})")
    for i, slot in enumerate(player.equipment): print(f"  スロット{i+1} Mana: {int(slot['mana'])}/{player.max_mana} {get_gauge_bar(slot['mana'], player.max_mana)}")
    if enemies:
        print("---")
        for i, enemy in enumerate(enemies):
            if not enemy.is_alive(): continue
            attack_bar = get_gauge_bar(enemy.attack_gauge, enemy.attack_interval)
            stats=f"攻:{enemy.attack}/防:{enemy.defense}"; status_list=[f"[{k.upper()}:{int(v['duration'])}s]" for k,v in enemy.status_effects.items()]
            if enemy.paralyzed_turns > 0: status_list.append(f"[麻痺:{enemy.paralyzed_turns}]")
            status=" ".join(status_list); buildup=f"[火:{enemy.elemental_buildup['火']} 水:{enemy.elemental_buildup['水']} 雷:{enemy.elemental_buildup['雷']} 土:{enemy.elemental_buildup['土']}]"
            print(f"【{i+1}:{enemy.name}】 HP:{enemy.hp}/{enemy.max_hp} {get_gauge_bar(enemy.hp, enemy.max_hp)} ATB: {attack_bar}")
            print(f"  {stats} {status}"); print(f"  属性蓄積: {buildup}")
    print("---")

def management_phase(player):
    player.update_stats_by_relics(); player.hp = min(player.hp, player.max_hp)
    while True:
        clear_screen(); print("== 管理フェーズ =="); print(f"現在の魔石: {player.stones}個"); display_status(player, [])
        print("\n1: 装備を変更\n2: 遺物を管理\n3: ショップへ行く\n4: 次の敵と戦う")
        choice = input("> ")
        if choice == '1': equip_phase(player)
        elif choice == '2': relic_phase(player)
        elif choice == '3': shop_phase(player)
        elif choice == '4': return

def equip_phase(player):
    while True:
        clear_screen(); print("== 装備の管理 =="); display_status(player, [])
        print("\n--- 現在の構成 ---")
        core_spell_name = player.core_slot["spell"].name if player.core_slot["spell"] else "空"
        print(f"コア: [{core_spell_name}]")
        for i, slot in enumerate(player.equipment):
            disk_name = slot["disk"].name if slot["disk"] else "空"
            spell_name = slot["spell"].name if slot["spell"] else "空"
            print(f"スロット{i+1}: [ディスク: {disk_name}] - [スペル: {spell_name}]")
        print("--------------------")
        print("\n1: コアスロットのスペルを変更")
        print("2: 装備スロットを変更")
        print("3: 戻る")
        choice = input("> ")
        if choice == '1':
            print("\n--- コアに装備するスペルを選択 --- (0: 装備しない)")
            for i, spell in enumerate(player.owned_spells): print(f"{i+1}: {spell.name} - {spell.description}")
            try:
                spell_choice_idx = int(input("> ")) - 1
                current_spell = player.core_slot["spell"]
                if spell_choice_idx == -1:
                    if current_spell: player.owned_spells.append(current_spell)
                    player.core_slot["spell"] = None
                elif 0 <= spell_choice_idx < len(player.owned_spells):
                    if current_spell: player.owned_spells.append(current_spell)
                    player.core_slot["spell"] = player.owned_spells.pop(spell_choice_idx)
            except (ValueError, IndexError): print("無効な入力です。")
        elif choice == '2':
            try:
                slot_idx = int(input(f"変更するスロット番号 (1-{len(player.equipment)}): ")) - 1
                if not (0 <= slot_idx < len(player.equipment)): raise ValueError
                target_slot = player.equipment[slot_idx]
                print("\n1: ディスクを変更\n2: スペルを変更")
                part_choice = input("> ")
                if part_choice == '1':
                    print("\n--- 装備するディスクを選択 --- (0: 装備しない)")
                    for i, disk in enumerate(player.owned_disks): print(f"{i+1}: {disk.name} - {disk.description}")
                    item_choice_idx = int(input("> ")) - 1
                    current_item = target_slot["disk"]
                    if item_choice_idx == -1:
                        if current_item: player.owned_disks.append(current_item)
                        target_slot["disk"] = None
                    elif 0 <= item_choice_idx < len(player.owned_disks):
                        if current_item: player.owned_disks.append(current_item)
                        target_slot["disk"] = player.owned_disks.pop(item_choice_idx)
                elif part_choice == '2':
                    print("\n--- 装備するスペルを選択 --- (0: 装備しない)")
                    for i, spell in enumerate(player.owned_spells): print(f"{i+1}: {spell.name} - {spell.description}")
                    item_choice_idx = int(input("> ")) - 1
                    current_item = target_slot["spell"]
                    if item_choice_idx == -1:
                        if current_item: player.owned_spells.append(current_item)
                        target_slot["spell"] = None
                    elif 0 <= item_choice_idx < len(player.owned_spells):
                        if current_item: player.owned_spells.append(current_item)
                        target_slot["spell"] = player.owned_spells.pop(item_choice_idx)
            except (ValueError, IndexError): print("無効な入力です。")
        elif choice == '3': return

def relic_phase(player):
    while True:
        clear_screen(); print("== 遺物の管理 ==")
        for i, relic in enumerate(player.relic_slots):
            relic_name = relic.name if relic else "空"
            print(f"遺物スロット{i+1}: {relic_name}")
        print("--------------------")
        try:
            slot_idx = int(input(f"変更するスロット番号 (1-{len(player.relic_slots)}, 0=戻る): ")) - 1
            if slot_idx == -1: return
            if not (0 <= slot_idx < len(player.relic_slots)): raise ValueError
            print("\n--- 装備する遺物を選択 --- (0: 装備しない)")
            for i, r in enumerate(player.owned_relics): print(f"{i+1}: {r.name} - {r.description}")
            relic_choice_idx = int(input("> ")) - 1
            current_relic = player.relic_slots[slot_idx]
            if relic_choice_idx == -1:
                if current_relic: player.owned_relics.append(current_relic)
                player.relic_slots[slot_idx] = None
            elif 0 <= relic_choice_idx < len(player.owned_relics):
                if current_relic: player.owned_relics.append(current_relic)
                player.relic_slots[slot_idx] = player.owned_relics.pop(relic_choice_idx)
            player.update_stats_by_relics()
        except (ValueError, IndexError): print("無効な入力。")

def shop_phase(player):
    DISK_COST, SPELL_COST, RELIC_COST, HEAL_COST = 20, 20, 75, 30
    while True:
        slot_cost = 50 * (len(player.equipment) - 2)
        clear_screen(); print("== ショップ =="); print(f"現在の魔石: {player.stones}個")
        print(f"\n1: ディスクを得る({DISK_COST})\n2: スペルを得る({SPELL_COST})\n3: 遺物を得る({RELIC_COST})\n4: アイテム売却\n5: スロット拡張({slot_cost})\n6: HP回復({HEAL_COST})\n7: 戻る")
        choice = input("> ")
        if choice == '1' and player.stones >= DISK_COST:
            player.stones -= DISK_COST; new_item = random.choice(ALL_DISKS); player.owned_disks.append(new_item); print(f"\nディスク『{new_item.name}』を得た！")
        elif choice == '2' and player.stones >= SPELL_COST:
            player.stones -= SPELL_COST; new_item = random.choice(ALL_SPELLS); player.owned_spells.append(new_item); print(f"\nスペル『{new_item.name}』を得た！")
        elif choice == '3' and player.stones >= RELIC_COST:
            player.stones -= RELIC_COST; new_item = random.choice(ALL_RELICS); player.owned_relics.append(new_item); print(f"\n遺物『{new_item.name}』を得た！")
        elif choice == '4':
            while True:
                clear_screen(); print("== アイテム売却 ==")
                print(f"1: ディスク売却 (売値:{DISK_SELL_PRICE})")
                print(f"2: スペル売却 (売値:{SPELL_SELL_PRICE})")
                print(f"3: 遺物売却 (売値:{RELIC_SELL_PRICE})")
                print("4: 戻る")
                sell_choice = input("> ")
                if sell_choice == '1':
                    print("\n--- 売却するディスクを選択 --- (0: 戻る)")
                    for i, item in enumerate(player.owned_disks): print(f"{i+1}: {item.name}")
                    try:
                        item_idx = int(input("> ")) - 1
                        if 0 <= item_idx < len(player.owned_disks):
                            sold_item = player.owned_disks.pop(item_idx)
                            player.stones += DISK_SELL_PRICE
                            print(f"『{sold_item.name}』を売却し、{DISK_SELL_PRICE}魔石を得た。")
                    except (ValueError, IndexError): pass
                elif sell_choice == '2':
                    print("\n--- 売却するスペルを選択 --- (0: 戻る)")
                    for i, item in enumerate(player.owned_spells): print(f"{i+1}: {item.name}")
                    try:
                        item_idx = int(input("> ")) - 1
                        if 0 <= item_idx < len(player.owned_spells):
                            sold_item = player.owned_spells.pop(item_idx)
                            player.stones += SPELL_SELL_PRICE
                            print(f"『{sold_item.name}』を売却し、{SPELL_SELL_PRICE}魔石を得た。")
                    except (ValueError, IndexError): pass
                elif sell_choice == '3':
                    print("\n--- 売却する遺物を選択 --- (0: 戻る)")
                    for i, item in enumerate(player.owned_relics): print(f"{i+1}: {item.name}")
                    try:
                        item_idx = int(input("> ")) - 1
                        if 0 <= item_idx < len(player.owned_relics):
                            sold_item = player.owned_relics.pop(item_idx)
                            player.stones += RELIC_SELL_PRICE
                            print(f"『{sold_item.name}』を売却し、{RELIC_SELL_PRICE}魔石を得た。")
                    except (ValueError, IndexError): pass
                elif sell_choice == '4': break
        elif choice == '5' and player.stones >= slot_cost:
            player.stones -= slot_cost; player.equipment.append({"disk": None, "spell": None, "mana": 0}); player.relic_slots.append(None)
            print(f"\nスロットを拡張！(現在: {len(player.equipment)}スロット)")
        elif choice == '6' and player.stones >= HEAL_COST:
            player.stones -= HEAL_COST; player.heal(player.max_hp)
        elif choice == '7': return
        else: print("\n魔石が足りません。")
        input("\nEnterキーで続ける...")

# --- 戦闘ループ ---
def combat_loop(player, enemies):
    player.update_stats_by_relics(); player.hp = min(player.hp, player.max_hp); player.buffs = {}
    for slot in player.equipment: slot["mana"] = 0
    player.core_slot["mana"] = 0
    clear_screen(); print(f"=== 敵が現れた！ ==="); time.sleep(1)
    process_event(player, enemies, "combat_start", None)
    last_second_update = time.time()
    while player.is_alive() and any(e.is_alive() for e in enemies):
        player.core_slot["mana"] = min(player.max_mana, player.core_slot["mana"] + CORE_MANA_PER_SEC * GAME_TICK)
        cast_all_possible_spells(player, enemies)
        for enemy in enemies:
            if not enemy.is_alive(): continue
            if enemy.paralyzed_turns > 0: continue
            if enemy.skip_turns > 0: enemy.skip_turns -=1; print(f"{enemy.name}は時が止まっている！"); continue
            enemy.attack_gauge += GAME_TICK
            if enemy.attack_gauge >= enemy.attack_interval:
                enemy.attack_gauge = 0; print(f"{enemy.name} の攻撃！")
                if player.reflect_turns > 0: print("プリズムウォールが敵の攻撃を反射した！"); enemy.take_damage(enemy.attack); player.reflect_turns -= 1
                else:
                    if player.take_damage(enemy.attack): process_event(player, enemies, "on_low_hp", None)
                process_event(player, enemies, "on_damage", None)
        if time.time() - last_second_update >= 1.0:
            last_second_update = time.time()
            for relic in player.relic_slots:
                if relic and relic.effect_type == 'start_turn_buildup':
                    for e in enemies:
                        if e.is_alive(): e.elemental_buildup[relic.value['attribute']] += relic.value['amount']
                if relic and relic.effect_type == 'start_turn_heal': player.heal(relic.value)
            for e in enemies: e.apply_timed_effects()
            for buff_type in list(player.buffs.keys()):
                player.buffs[buff_type]['duration'] -= 1
                if player.buffs[buff_type]['duration'] <= 0: print(f"{buff_type}上昇の効果が切れた。"); del player.buffs[buff_type]
            for e in list(e for e in enemies if e.paralyzed_turns > 0): e.paralyzed_turns -=1
        clear_screen(); display_status(player, enemies); time.sleep(GAME_TICK)

    if player.is_alive():
        total_stones = sum(e.stone_reward for e in enemies); print(f"\n戦闘に勝利した！");
        gained = player.add_stones(total_stones); print(f"魔石を {gained}個 手に入れた！")
        process_event(player, [], "on_stone_gain", None)
        if random.random() < 0.25: heal_amount=int(player.max_hp*0.5);player.heal(heal_amount);print(f"勝利の祝福！HPが回復！")
        if random.random() < 0.05:
            dropped_relic = random.choice(ALL_RELICS); player.owned_relics.append(dropped_relic)
            print(f"！！！なんと、敵は希少な遺物『{dropped_relic.name}』を落とした！")
    else: print("\nあなたは倒れてしまった...")
    input("\nEnterキーを押して続ける...")

def main():
    player = Player()
    encounters = [
        [Enemy("スライム", 60, 10, 0, 20, 4.0)], [Enemy("ゴブリン", 90, 15, 2, 25, 3.5)],
        [Enemy("オーク", 160, 20, 5, 40, 5.0)],
        [Enemy("ゴブリン", 90, 15, 2, 25, 3.5), Enemy("ゴブリン", 90, 15, 2, 25, 4.5)],
        [Enemy("リザードマン", 220, 25, 8, 50, 4.0)], [Enemy("ゴーレム", 350, 18, 15, 65, 6.0)],
        [Enemy("オーク", 160, 20, 5, 40, 5.0), Enemy("ゴブリン", 90, 15, 2, 25, 3.5)],
        [Enemy("ドラゴン", 500, 40, 10, 100, 5.5)],
    ]
    encounter_level = 0
    clear_screen(); print("========================"); print("SPELL DISK CLI v15 (RTB)"); print("========================")
    input("Enterキーでゲーム開始...")
    while player.is_alive():
        management_phase(player)
        if encounter_level < len(encounters):
            # 敵のコピーを作成する際に、コンストラクタに渡す引数を明示的に指定
            enemy_templates = encounters[encounter_level]
            current_enemies = [Enemy(e.name, e.hp, e.attack, e.defense, e.stone_reward, e.attack_interval) for e in enemy_templates]
            encounter_level += 1
        else:
            last = encounters[-1][-1]; current_enemies = [Enemy(f"強化{last.name}", int(last.max_hp*1.5), int(last.attack*1.2), int(last.defense*1.2), int(last.stone_reward*1.5), last.attack_interval*0.8)]
        player.defense = 0
        combat_loop(player, current_enemies)
    print("\nゲームオーバー")

if __name__ == "__main__":
    main()

