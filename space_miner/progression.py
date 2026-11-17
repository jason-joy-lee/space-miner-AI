"""Server-derived mission milestones and post-mining feedback.

Achievements are based on actual actions; they never change the hidden ore
labels, manipulate KNN predictions, or inject free game credits.
"""


def challenge_board(m):
    histories = m.history
    correctness = sum(bool(row["ore"]) for row in histories)
    incorrect_labels = sum(not x["correct"] for x in m.label_audit)
    verified = len(m.scanned)
    corrected_ai = any(
        row.get("player_guess") is not None
        and row.get("guess_correct") is True
        and (row["player_guess"] == "ore") != row["predicted"]
        for row in histories
    )
    # Requires an actual training/evaluation experiment, not just a saved A.
    model_experiment = bool(m.model_experiments)
    definitions = (
        ("first_signal", "First Signal", "Train your first model", bool(m.training_runs), "Choose K and train."),
        ("field_researcher", "Field Researcher", "Inspect 3 different planets", len(m.inspected_ids) >= 3, f"{len(m.inspected_ids)} / 3 inspected"),
        ("label_apprentice", "Label Apprentice", "Annotate a training report", bool(m.labeled_ids), "Make a provisional label."),
        ("data_detective", "Data Detective", "Find and verify one wrong label", incorrect_labels >= 1, f"{incorrect_labels} incorrect labels corrected"),
        ("model_engineer", "Model Engineer", "Compare two different trained models", model_experiment, "Save A; change K, focus or labels and train B."),
        ("ore_hunter", "Ore Hunter", "Discover ore on 3 worlds", correctness >= 3, f"{correctness} / 3 ore discoveries"),
        ("ai_critic", "AI Critic", "Correctly disagree with the AI", corrected_ai, "Make your own call on an AI prediction."),
    )
    return [
        {"id":key,"name":name,"objective":objective,"completed":completed,"hint":hint}
        for key,name,objective,completed,hint in definitions
    ]


def diagnostic_debrief(last):
    """Explain the *observed* last mistake, never leak unexplored labels."""
    if last is None:
        return None
    correct = last["predicted"] == last["ore"]
    provisional = [neighbor for neighbor in last.get("neighbors", []) if neighbor.get("provisional")]
    if not correct and provisional:
        reason = ("A contributing training label was provisional. It might be wrong, "
                  "so verify it before trusting the next decision.")
        next_steps = ["Verify a provisional voter via a training scan",
                      "Retrain and compare Model A vs B", "Inspect whether the nearest voters changed"]
    elif not correct:
        reason = ("Known planets with similar readings voted for the wrong class. "
                  "This can happen because of noisy labels or overlapping features.")
        next_steps = ["Save a baseline model and test another K value",
                      "Scan a nearby training report", "Compare the accuracy and changed predictions"]
    else:
        reason = ("The model majority matched this discovery, but one correct decision "
                  "does not prove the model generalizes.")
        next_steps = ["Review the K voters behind this choice",
                      "Test another K or sensor focus", "Look for a candidate where models disagree"]
    return {
        "planet_id":last["planet_id"],"predicted":last["predicted"],
        "actual":last["ore"],"prediction_correct":correct,
        "analysis":reason,"next_steps":next_steps,
        "voter_ids":[n["id"] for n in last.get("neighbors", [])],
        "provisional_voters":[n["id"] for n in provisional]
    }
