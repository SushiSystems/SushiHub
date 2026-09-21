/** @file GeneratedForm.hpp
 *  @brief Declares the form one catalogue command is drawn as, and the run its button starts.
 *  @author Mustafa Garip
 */

#pragma once

#include "contract/Catalogue.hpp"
#include "model/CommandRun.hpp"
#include "model/RunLog.hpp"
#include "ui/widgets/PromptDialog.hpp"

#include <array>
#include <cstddef>
#include <memory>
#include <string>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Draws one command's parameters as widgets and runs the command line they build. */
class GeneratedForm
{
public:
    /**
     * @brief Binds the form to @p command and to the executable a run is spawned from.
     * @param hub_executable The `hub` program, however the workspace found it.
     * @param run_log The log the activity strip reads, which every started run is adopted into.
     */
    GeneratedForm(Command command, std::string hub_executable, RunLog& run_log);

    /**
     * @brief Enters @p values into the command's positional arguments, in declaration order.
     * @param values One value per argument; extra values are dropped.
     */
    void prefill_arguments(const std::vector<std::string>& values);

    /** @brief Draws the parameter widgets, the Run button and the question a run stops on. */
    void draw();

    /** @brief Returns the command the form was generated from. */
    const Command& command() const;

private:
    /** @brief Holds how many characters one parameter's text may have, the terminator included. */
    static constexpr std::size_t TEXT_CAPACITY = 512;

    /** @brief Holds what one parameter's widget currently shows. */
    struct Field
    {
        /** @brief Holds the text of every parameter kind but the boolean, null-terminated. */
        std::array<char, TEXT_CAPACITY> text{};

        /** @brief Holds the state of a boolean parameter's checkbox. */
        bool flag = false;
    };

    /** @brief Fills every field with the default its parameter declares. */
    void adopt_defaults();

    /** @brief Draws the widget @p parameter's type asks for, over @p field. */
    void draw_field(const Parameter& parameter, Field& field);

    /** @brief Draws the combo of @p parameter's allowed values over @p field. */
    void draw_choice(const Parameter& parameter, Field& field);

    /** @brief Draws the Run button, the state that disables it and the run it starts. */
    void draw_controls();

    /** @brief Polls the started run and answers the question it stops on. */
    void draw_run();

    /** @brief Assembles the command line the Run button starts. */
    std::vector<std::string> build_argv() const;

    /** @brief Reports whether every required parameter has been given a value. */
    bool ready() const;

    /** @brief Holds the catalogue entry every widget is drawn from. */
    Command command_;

    /** @brief Holds the `hub` program a run is spawned from. */
    std::string hub_executable_;

    /** @brief Holds one field per parameter, in the order the command declares them. */
    std::vector<Field> fields_;

    /** @brief Holds the run the Run button started, null until it is pressed. */
    std::unique_ptr<CommandRun> run_;

    /** @brief Holds the log the strip reports this form's run from. */
    RunLog& run_log_;

    /** @brief Collects the answer to a question the run stops on. */
    Widgets::PromptDialog prompt_;
};

}
}
