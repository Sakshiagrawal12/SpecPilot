
from app.ai.description import description_generator
from app.ai.prd import prd_generator
from app.ai.task_generator import task_generator
from app.ai.sprint_generator import sprint_generator


class AIGenerator:

    def generate_all(self, project):

        print("==========================================")
        print("AI GENERATION START")
        print("==========================================")

        print(
            "Project ID:",
            project.id
        )

        print(
            "Project Name:",
            project.project_name
        )

        # =====================================================
        # 1. DESCRIPTION
        # =====================================================

        print("------------------------------------------")
        print("GENERATING DESCRIPTION")
        print("------------------------------------------")

        description = (
            description_generator.generate(
                project
            )
        )

        if not description:

            raise RuntimeError(
                "AI returned empty description."
            )

        print("Description generated successfully.")

        # =====================================================
        # 2. PRD
        # =====================================================

        print("------------------------------------------")
        print("GENERATING PRD")
        print("------------------------------------------")

        prd = (
            prd_generator.generate(
                project
            )
        )

        if not prd:

            raise RuntimeError(
                "AI returned empty PRD."
            )

        print("PRD generated successfully.")

        # =====================================================
        # 3. TASKS
        # =====================================================

        print("------------------------------------------")
        print("GENERATING TASKS")
        print("------------------------------------------")

        tasks = (
            task_generator.generate(
                project,
                prd
            )
        )

        if not tasks:

            raise RuntimeError(
                "AI returned no tasks."
            )

        print(
            "Tasks generated:",
            len(tasks)
        )

        # =====================================================
        # 4. SPRINT PLAN
        # =====================================================

        print("------------------------------------------")
        print("GENERATING SPRINT PLAN")
        print("------------------------------------------")

        sprint_plan = (
            sprint_generator.generate(
                project,
                tasks
            )
        )

        if not sprint_plan:

            raise RuntimeError(
                "AI returned empty sprint plan."
            )

        print("Sprint plan generated successfully.")

        print("==========================================")
        print("AI GENERATION COMPLETE")
        print("==========================================")

        return {
            "description": description,
            "prd": prd,
            "tasks": tasks,
            "sprint_plan": sprint_plan
        }


generator = AIGenerator()
