from __future__ import annotations

from app.modules.intelligence.aggregation.models import (
    CollaborationSection,
    DatasetSection,
    DiversityMetrics,
    InstitutionEntry,
    InstitutionSection,
    LandscapeResult,
    MethodologyEntry,
    MethodologySection,
    NetworkSection,
    Observation,
    OverviewSection,
    StatisticsSection,
    TechnologySection,
    TemporalSection,
)
from app.modules.intelligence.analyzers.models import AnalysisResults


class LandscapeAggregator:
    def aggregate(self, results: AnalysisResults) -> LandscapeResult:
        institution = results.results.get("institution")
        methodology = results.results.get("methodology")
        temporal = results.results.get("temporal")
        technology = results.results.get("technology")
        dataset = results.results.get("dataset")
        collaboration = results.results.get("collaboration")

        inst_data = institution.data if institution else {}
        meth_data = methodology.data if methodology else {}
        temp_data = temporal.data if temporal else {}
        tech_data = technology.data if technology else {}
        ds_data = dataset.data if dataset else {}
        collab_data = collaboration.data if collaboration else {}

        overview = self._build_overview(
            inst_data,
            meth_data,
            tech_data,
            ds_data,
            collab_data,
            temp_data,
        )
        institutions_sec = self._build_institution_section(inst_data)
        methodologies_sec = self._build_methodology_section(meth_data)
        technologies_sec = self._build_technology_section(tech_data)
        datasets_sec = self._build_dataset_section(ds_data)
        temporal_sec = self._build_temporal_section(temp_data)
        collaborations_sec = self._build_collaboration_section(collab_data)
        statistics_sec = self._build_statistics_section(temp_data)
        observations = self._build_observations(
            inst_data,
            meth_data,
            tech_data,
            ds_data,
            collab_data,
            temp_data,
        )

        return LandscapeResult(
            overview=overview,
            institutions=institutions_sec,
            methodologies=methodologies_sec,
            technologies=technologies_sec,
            datasets=datasets_sec,
            temporal=temporal_sec,
            collaborations=collaborations_sec,
            statistics=statistics_sec,
            observations=observations,
        )

    # ── Section builders ──────────────────────────────────────────

    @staticmethod
    def _build_overview(
        inst: dict,
        meth: dict,
        tech: dict,
        ds: dict,
        collab: dict,
        temp: dict,
    ) -> OverviewSection:
        return OverviewSection(
            total_papers=temp.get("total_papers", 0),
            years_covered=temp.get("years_covered", []),
            total_institutions=inst.get("total_institutions", 0),
            total_methodologies=meth.get("total_methodologies", 0),
            total_technologies=tech.get("diversity", {}).get("total_technologies", 0),
            total_datasets=ds.get("diversity", {}).get("total_datasets", 0),
            total_authors=collab.get("author_network", {}).get("total_authors", 0),
        )

    @staticmethod
    def _build_institution_section(data: dict) -> InstitutionSection:
        if not data:
            return InstitutionSection()

        top_raw = _safe_list(data, "top_institutions")
        top = [
            InstitutionEntry(
                name=e["name"],
                type=e["type"],
                paper_count=e["paper_count"],
                author_count=e["author_count"],
            )
            for e in top_raw
            if isinstance(e, dict)
        ]

        by_type_raw = data.get("institutions_by_type", {})
        by_type: dict[str, list[InstitutionEntry]] = {}
        if isinstance(by_type_raw, dict):
            for t, entries in by_type_raw.items():
                if isinstance(entries, list):
                    by_type[t] = [
                        InstitutionEntry(
                            name=e["name"],
                            type=e["type"],
                            paper_count=e["paper_count"],
                            author_count=e["author_count"],
                        )
                        for e in entries
                        if isinstance(e, dict)
                    ]

        total = data.get("total_institutions", 0)
        if not isinstance(total, int):
            total = 0
        type_dist = data.get("institution_type_distribution", {})
        if not isinstance(type_dist, dict):
            type_dist = {}

        return InstitutionSection(
            total=total,
            type_distribution=type_dist,
            top_institutions=top,
            institutions_by_type=by_type,
        )

    @staticmethod
    def _build_methodology_section(data: dict) -> MethodologySection:
        if not data:
            return MethodologySection()

        top_raw = data.get("methodologies", [])
        top = [
            MethodologyEntry(
                name=e["name"],
                paper_count=e["paper_count"],
                technique_count=e["technique_count"],
                techniques=e.get("techniques", []),
            )
            for e in top_raw
        ]

        return MethodologySection(
            total=data.get("total_methodologies", 0),
            top_methodologies=top,
        )

    @staticmethod
    def _build_technology_section(data: dict) -> TechnologySection:
        if not data:
            return TechnologySection()

        div_raw = data.get("diversity", {})
        if not isinstance(div_raw, dict):
            div_raw = {}

        tech_total = div_raw.get("total_technologies", 0)
        if not isinstance(tech_total, int):
            tech_total = 0
        tech_papers = div_raw.get("papers_with_technology", 0)
        if not isinstance(tech_papers, int):
            tech_papers = 0
        tech_avg = float(div_raw.get("avg_papers_per_technology", 0.0) or 0)

        first_appearance = data.get("first_appearance_by_year", {})
        if not isinstance(first_appearance, dict):
            first_appearance = {}

        return TechnologySection(
            total=tech_total,
            top_technologies=_safe_list(data, "top_technologies"),
            first_appearance_by_year=first_appearance,
            diversity=DiversityMetrics(
                total=tech_total,
                papers_with_entity=tech_papers,
                avg_papers_per_entity=tech_avg,
            ),
        )

    @staticmethod
    def _build_dataset_section(data: dict) -> DatasetSection:
        if not data:
            return DatasetSection()

        div_raw = data.get("diversity", {})
        if not isinstance(div_raw, dict):
            div_raw = {}

        ds_total = div_raw.get("total_datasets", 0)
        if not isinstance(ds_total, int):
            ds_total = 0
        ds_papers = div_raw.get("papers_with_dataset", 0)
        if not isinstance(ds_papers, int):
            ds_papers = 0
        ds_avg = float(div_raw.get("avg_papers_per_dataset", 0.0) or 0)

        yearly_usage = data.get("yearly_usage_trends", {})
        if not isinstance(yearly_usage, dict):
            yearly_usage = {}

        return DatasetSection(
            total=ds_total,
            top_datasets=_safe_list(data, "top_datasets"),
            yearly_usage_trends=yearly_usage,
            diversity=DiversityMetrics(
                total=ds_total,
                papers_with_entity=ds_papers,
                avg_papers_per_entity=ds_avg,
            ),
        )

    @staticmethod
    def _build_temporal_section(data: dict) -> TemporalSection:
        return TemporalSection(
            years_covered=data.get("years_covered", []),
            papers_per_year=data.get("papers_per_year", {}),
            total_papers=data.get("total_papers", 0),
        )

    @staticmethod
    def _build_collaboration_section(data: dict) -> CollaborationSection:
        inst_net_raw = data.get("institution_network", {})
        author_net_raw = data.get("author_network", {})

        return CollaborationSection(
            institution_network=NetworkSection(
                total_nodes=inst_net_raw.get("total_institutions", 0),
                total_edges=inst_net_raw.get("total_collaborations", 0),
                degree_centrality=inst_net_raw.get("degree_centrality", {}),
                top_by_centrality=inst_net_raw.get("top_by_centrality", []),
            ),
            author_network=NetworkSection(
                total_nodes=author_net_raw.get("total_authors", 0),
                total_edges=author_net_raw.get("total_collaborations", 0),
                degree_centrality=author_net_raw.get("degree_centrality", {}),
                top_by_centrality=author_net_raw.get("top_by_centrality", []),
            ),
            top_institution_collaborations=data.get(
                "institution_collaborations",
                [],
            ),
            top_author_collaborations=data.get("author_collaborations", []),
        )

    @staticmethod
    def _build_statistics_section(data: dict) -> StatisticsSection:
        return StatisticsSection(
            papers_per_year=data.get("papers_per_year", {}),
            total_papers=data.get("total_papers", 0),
        )

    # ── Observations ──────────────────────────────────────────────

    @staticmethod
    def _build_observations(
        inst: dict,
        meth: dict,
        tech: dict,
        ds: dict,
        collab: dict,
        temp: dict,
    ) -> list[Observation]:
        obs: list[Observation] = []

        top_inst = _safe_list(inst, "top_institutions")
        if top_inst:
            e = top_inst[0]
            obs.append(
                Observation(
                    category="institution",
                    label="Most active institution",
                    value=f"{e['name']} ({e['paper_count']} papers)",
                )
            )

        type_dist = inst.get("institution_type_distribution", {})
        if len(type_dist) > 1:
            most_common_type = max(type_dist, key=type_dist.get)
            obs.append(
                Observation(
                    category="institution",
                    label="Most common institution type",
                    value=f"{most_common_type} ({type_dist[most_common_type]} institutions)",
                )
            )

        top_meth = _safe_list(meth, "methodologies")
        if top_meth:
            e = top_meth[0]
            obs.append(
                Observation(
                    category="methodology",
                    label="Most common methodology",
                    value=f"{e['name']} ({e['paper_count']} papers)",
                )
            )

        total_meth = meth.get("total_methodologies", 0)
        if total_meth:
            obs.append(
                Observation(
                    category="methodology",
                    label="Methodology diversity",
                    value=f"{total_meth} distinct methodologies used",
                )
            )

        top_tech = _safe_list(tech, "top_technologies")
        if top_tech:
            obs.append(
                Observation(
                    category="technology",
                    label="Most used technology",
                    value=f"{top_tech[0][0]} ({top_tech[0][1]} papers)",
                )
            )

        first_year_map = tech.get("first_appearance_by_year", {})
        if first_year_map:
            latest = max(first_year_map.items(), key=lambda x: x[1] or 0)
            if latest[1] is not None:
                obs.append(
                    Observation(
                        category="technology",
                        label="Newest technology",
                        value=f"{latest[0]} (first appeared {latest[1]})",
                    )
                )

        tech_div = tech.get("diversity", {})
        if tech_div.get("total_technologies", 0):
            avg = tech_div.get("avg_papers_per_technology", 0.0)
            obs.append(
                Observation(
                    category="technology",
                    label="Technology adoption rate",
                    value=f"{avg} papers per technology on average",
                )
            )

        top_ds = _safe_list(ds, "top_datasets")
        if top_ds:
            obs.append(
                Observation(
                    category="dataset",
                    label="Most used dataset",
                    value=f"{top_ds[0][0]} ({top_ds[0][1]} papers)",
                )
            )

        ds_div = ds.get("diversity", {})
        if ds_div.get("total_datasets", 0):
            avg = ds_div.get("avg_papers_per_dataset", 0.0)
            obs.append(
                Observation(
                    category="dataset",
                    label="Dataset reuse rate",
                    value=f"{avg} papers per dataset on average",
                )
            )

        years = temp.get("years_covered", [])
        if len(years) >= 1:
            span = f"{years[0]}" if len(years) == 1 else f"{years[0]}–{years[-1]}"
            obs.append(
                Observation(
                    category="temporal",
                    label="Research time span",
                    value=span,
                )
            )

        total_papers = temp.get("total_papers", 0)
        if total_papers:
            obs.append(
                Observation(
                    category="temporal",
                    label="Total research output",
                    value=f"{total_papers} papers in corpus",
                )
            )

        collab_inst = collab.get("institution_network", {})
        tot_inst = collab_inst.get("total_institutions", 0)
        tot_collabs = collab_inst.get("total_collaborations", 0)
        if tot_inst:
            rate = round(tot_collabs / max(tot_inst, 1), 2)
            obs.append(
                Observation(
                    category="collaboration",
                    label="Institution collaboration intensity",
                    value=f"{rate} collaborations per institution",
                )
            )

        collab_author = collab.get("author_network", {})
        auth_edges = collab_author.get("total_collaborations", 0)
        if auth_edges:
            obs.append(
                Observation(
                    category="collaboration",
                    label="Author collaboration network",
                    value=f"{auth_edges} co-authorship connections",
                )
            )

        return obs


def _safe_list(data: dict, key: str) -> list:
    val = data.get(key, [])
    return val if isinstance(val, list) else []
