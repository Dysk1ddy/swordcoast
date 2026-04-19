from __future__ import annotations


class StoryAct3ScaffoldMixin:
    ACT3_PROFILE_OPTIONS = (
        "mercy_first",
        "institution_first",
        "route_first",
        "secrecy_first",
        "force_first",
        "chaos_first",
        "balanced",
    )

    def act3_clamp(self, value: int, *, lower: int = 0, upper: int = 5) -> int:
        return max(lower, min(upper, value))

    def malzurath_revealed(self) -> bool:
        assert self.state is not None
        return bool(self.state.flags.get("malzurath_revealed"))

    def act3_map_integrity(self) -> int:
        assert self.state is not None
        flags = self.state.flags
        integrity = 2
        if flags.get("act1_victory_tier") == "clean_victory":
            integrity += 1
        if flags.get("act3_claims_balance") == "secured":
            integrity += 1
        if flags.get("act3_forge_route_state") in {"mastered", "broken"}:
            integrity += 1
        if flags.get("act3_forge_lens_state") == "mapped":
            integrity += 1
        if flags.get("act3_whisper_state") == "carried_out":
            integrity -= 1
        return self.act3_clamp(integrity)

    def act3_player_pattern_profile(self) -> str:
        assert self.state is not None
        flags = self.state.flags
        scores = {
            "mercy_first": 0,
            "institution_first": 0,
            "route_first": 0,
            "secrecy_first": 0,
            "force_first": 0,
            "chaos_first": 0,
        }

        if flags.get("pattern_preserves_people"):
            scores["mercy_first"] += 3
        if flags.get("pattern_preserves_institutions"):
            scores["institution_first"] += 3
        if flags.get("pattern_hunts_systems"):
            scores["route_first"] += 3

        if flags.get("bryn_ledger_burned"):
            scores["secrecy_first"] += 1
        if flags.get("bryn_ledger_sold"):
            scores["force_first"] += 1
        if flags.get("elira_mercy_blessing") or flags.get("quest_reward_elira_mercy_blessing"):
            scores["mercy_first"] += 1
        if flags.get("elira_hard_verdict"):
            scores["force_first"] += 1

        sponsor = str(flags.get("act2_sponsor", "council"))
        if sponsor == "exchange":
            scores["secrecy_first"] += 1
        elif sponsor == "lionshield":
            scores["institution_first"] += 1
        elif sponsor == "wardens":
            scores["mercy_first"] += 1

        first_late_route = str(flags.get("act2_first_late_route", "")).strip()
        if first_late_route == "broken_prospect":
            scores["route_first"] += 1
        elif first_late_route == "south_adit":
            scores["mercy_first"] += 1

        if flags.get("act2_infiltrator_escaped") or flags.get("act3_whisper_state") == "carried_out":
            scores["chaos_first"] += 1

        top_score = max(scores.values())
        if top_score <= 0:
            return "balanced"
        winners = [profile for profile, score in scores.items() if score == top_score]
        if len(winners) == 1:
            return winners[0]
        return "balanced"

    def act3_unrecorded_choice_tokens(self) -> int:
        assert self.state is not None
        flags = self.state.flags
        tokens = 0
        if flags.get("counter_cadence_known"):
            tokens += 1
        if flags.get("act3_lens_understood") or flags.get("act3_forge_lens_state") == "mapped":
            tokens += 1
        if flags.get("bryn_ledger_burned"):
            tokens += 1
        if flags.get("elira_mercy_blessing") or flags.get("quest_reward_elira_mercy_blessing"):
            tokens += 1

        resolved_arc_flags = (
            "bryn_loose_ends_resolved",
            "elira_faith_under_ash_resolved",
            "act1_companion_conflict_resolved",
        )
        tokens += min(2, sum(1 for flag_name in resolved_arc_flags if flags.get(flag_name)))

        trusted_companions = sum(1 for companion in self.state.all_companions() if companion.disposition >= 6)
        tokens += min(2, trusted_companions)
        return self.act3_clamp(tokens)

    def act3_hidden_pressure_label(self) -> str:
        assert self.state is not None
        if self.malzurath_revealed():
            return "Ninth Ledger Pressure"
        if self.state.flags.get("act3_signal_carried") or self.state.flags.get("act3_whisper_state") == "carried_out":
            return "Signal Pressure"
        if self.state.flags.get("act3_whisper_state") == "lingering":
            return "Whisper Pressure"
        return "Map Pressure"

    def act3_record_scaffold_flags(self) -> None:
        assert self.state is not None
        self.state.current_act = max(self.state.current_act, 3)
        self.state.flags["act3_started"] = True
        self.state.flags.setdefault("malzurath_revealed", False)
        self.state.flags["act3_map_integrity"] = self.act3_map_integrity()
        self.state.flags["player_pattern_profile"] = self.act3_player_pattern_profile()
        self.state.flags["act3_varyn_apparent_primary"] = not self.malzurath_revealed()
        self.state.flags["unrecorded_choice_tokens"] = self.act3_unrecorded_choice_tokens()
        if not self.malzurath_revealed():
            self.state.flags.pop("ninth_ledger_pressure", None)

    # ACT3_POST_REVEAL_TEXT_START
    def act3_ninth_ledger_pressure(self) -> int:
        assert self.state is not None
        flags = self.state.flags
        pressure = 2
        if flags.get("act3_signal_carried"):
            pressure += 1
        if flags.get("act3_whisper_state") == "carried_out":
            pressure += 1
        if flags.get("act3_lens_blinded") or flags.get("act3_forge_lens_state") == "shattered_blind":
            pressure += 1
        if int(flags.get("act3_map_integrity", self.act3_map_integrity()) or 0) <= 1:
            pressure += 1
        if flags.get("act3_lens_understood") or flags.get("act3_forge_lens_state") == "mapped":
            pressure -= 1
        if flags.get("counter_cadence_known"):
            pressure -= 1
        pressure -= int(flags.get("act3_reveal_resistance_bonus", 0) or 0)
        return self.act3_clamp(pressure)

    def act3_refresh_post_reveal_state(self) -> None:
        assert self.state is not None
        if not self.malzurath_revealed():
            return
        self.state.flags["act3_varyn_apparent_primary"] = False
        self.state.flags["unrecorded_choice_tokens"] = self.act3_unrecorded_choice_tokens()
        self.state.flags["ninth_ledger_pressure"] = self.act3_ninth_ledger_pressure()

    def act3_use_unrecorded_choice_token(self, reason: str = "") -> bool:
        assert self.state is not None
        if not self.malzurath_revealed():
            return False
        tokens = int(self.state.flags.get("unrecorded_choice_tokens", self.act3_unrecorded_choice_tokens()) or 0)
        if tokens <= 0:
            return False
        self.state.flags["unrecorded_choice_tokens"] = tokens - 1
        if reason:
            self.add_journal(f"Unrecorded choice spent: {reason}")
        return True

    def act3_reveal_voice_line(self) -> None:
        assert self.state is not None
        if self.find_companion("Irielle Ashwake") is not None:
            self.speaker(
                "Irielle Ashwake",
                "That is not Choir scripture. That is Malzurath, Keeper of the Ninth Ledger. I heard the name once and watched three people forget they had mouths.",
            )
            return
        if self.find_companion("Nim Ardentglass") is not None:
            self.speaker(
                "Nim Ardentglass",
                "Caldra's math was missing a signature. This is it: Malzurath, Keeper of the Ninth Ledger. The Forge was a lens because the Ledger needed eyes.",
            )
            return
        self.say(
            "The page writes the name with surgical patience: Malzurath, Keeper of the Ninth Ledger. Every route you thought was merely watched was also being balanced."
        )

    def scene_act3_ninth_ledger_opens(self) -> None:
        assert self.state is not None
        self.act3_record_scaffold_flags()
        profile = str(self.state.flags.get("player_pattern_profile", self.act3_player_pattern_profile()))
        map_integrity = int(self.state.flags.get("act3_map_integrity", self.act3_map_integrity()) or 0)

        self.banner("The Ninth Ledger Opens")
        self.say(
            "You corner Varyn inside a living map: roads made of ink, witness names pinned like stars, and one route pulsing where no road has ever been surveyed.",
            typed=True,
        )
        self.speaker(
            "Varyn Sable",
            f"I know your pattern now. {profile.replace('_', ' ').title()}. That should have been enough.",
        )
        self.say(
            "Then the map writes a new road through the table. It crosses no hill, no tunnel, no gate. It crosses the next choice you have not made yet."
        )
        choice = self.scenario_choice(
            "How do you answer the page that already thinks it owns the next decision?",
            [
                self.skill_tag("ARCANA", self.action_option("Break the route's counted grammar before it finishes writing you.")),
                self.skill_tag("INSIGHT", self.action_option("Name the part of the map Varyn did not design.")),
                self.action_option("Hold a contradiction in both hands and refuse to make it tidy."),
            ],
            allow_meta=False,
        )

        resistance_bonus = 0
        if choice == 1:
            self.player_action("Break the route's counted grammar before it finishes writing you.")
            dc = max(12, 16 - map_integrity)
            if self.skill_check(self.state.player, "Arcana", dc, context="to break the ledger route's counted grammar"):
                resistance_bonus = 2
                self.state.flags["act3_reveal_route_grammar_broken"] = True
                self.say("Ink buckles away from your hand, and one line of the future becomes only wet black thread.")
        elif choice == 2:
            self.player_action("Name the part of the map Varyn did not design.")
            dc = max(12, 15 - int(bool(self.state.flags.get("act3_lens_understood"))))
            if self.skill_check(self.state.player, "Insight", dc, context="to separate Varyn's mapwork from the stranger route"):
                resistance_bonus = 1
                self.state.flags["act3_reveal_false_author_named"] = True
                self.say("Varyn flinches before the page does. That is the answer: for once, both of you are being read.")
        else:
            self.player_action("Hold a contradiction in both hands and refuse to make it tidy.")
            resistance_bonus = 1
            if self.state.flags.get("counter_cadence_known"):
                resistance_bonus += 1
                self.say("The counter-cadence catches under your breath, ugly and alive, and the page fails to make the contradiction close.")
            else:
                self.say("The page hesitates. It can record a decision, but not the shape of refusing its premise.")

        self.speaker("Varyn Sable", "No. That route is not mine.")
        self.say(
            "A page turns where there is no book. It records a choice you have not made, assigns it a cost, and files the cost under your name."
        )
        self.act3_reveal_voice_line()

        self.state.flags["malzurath_revealed"] = True
        self.state.flags["act3_ninth_ledger_opened"] = True
        self.state.flags["act3_varyn_apparent_primary"] = False
        self.state.flags["act3_reveal_profile_named"] = profile
        self.state.flags["act3_reveal_resistance_bonus"] = resistance_bonus
        self.act3_refresh_post_reveal_state()
        self.add_clue("Malzurath, Keeper of the Ninth Ledger, has been using route logic, Forge resonance, and recorded choices as an accounting system.")
        self.add_journal(
            f"The Ninth Ledger is open. Pressure: {self.state.flags['ninth_ledger_pressure']}/5. "
            f"Unrecorded choices: {self.state.flags['unrecorded_choice_tokens']}."
        )
        self.say(
            f"The hidden pressure becomes visible: {self.act3_hidden_pressure_label()} {self.state.flags['ninth_ledger_pressure']}/5. "
            f"You have {self.state.flags['unrecorded_choice_tokens']} unrecorded choice token(s) to spend against recorded outcomes."
        )
        self.state.current_scene = "act3_ninth_ledger_aftermath"

    def scene_act3_ninth_ledger_aftermath(self) -> None:
        assert self.state is not None
        self.banner("Act III: Ledger Aftermath")
        self.act3_refresh_post_reveal_state()
        self.say(
            f"The Ninth Ledger is visible now. Pressure sits at {self.state.flags.get('ninth_ledger_pressure', 0)}/5, "
            f"and {self.state.flags.get('unrecorded_choice_tokens', 0)} unrecorded choice token(s) remain for future Act 3 scenes."
        )
        self.say("The full post-reveal route is still being planned, but the campaign state now has the mechanics it needs.")
    # ACT3_POST_REVEAL_TEXT_END
