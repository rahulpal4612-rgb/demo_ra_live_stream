def reciprocal_rank_fusion(
    result_lists: list[list[dict]],
    k: int = 60
) -> list[dict]:

    fused_scores = {}
    results_by_chunk = {}

    for results in result_lists:
        for rank, result in enumerate(results, start=1):

            chunk_id = result["metadata"]["chunk_id"]

            if chunk_id not in fused_scores:
                fused_scores[chunk_id] = 0.0
                results_by_chunk[chunk_id] = result

            fused_scores[chunk_id] += 1 / (k + rank)

    ranked_chunk_ids = sorted(
        fused_scores,
        key=fused_scores.get,
        reverse=True
    )

    fused_results = []

    for chunk_id in ranked_chunk_ids:
        result = results_by_chunk[chunk_id].copy()

        result["fusion_score"] = fused_scores[chunk_id]

        fused_results.append(result)

    return fused_results