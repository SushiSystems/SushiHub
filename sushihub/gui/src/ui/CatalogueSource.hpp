/** @file CatalogueSource.hpp
 *  @brief Declares the one-off read of `ss --describe` the sidebar's command list comes from.
 *  @author Mustafa Garip
 */

#pragma once

#include "bridge/LineQueue.hpp"
#include "bridge/Process.hpp"
#include "contract/Catalogue.hpp"

#include <memory>
#include <string>

namespace SushiHub
{
namespace Gui
{

/** @brief Runs `ss --describe` once and hands back the catalogue it prints. */
class CatalogueSource
{
public:
    /** @brief Binds the source to the `ss` program the catalogue is read from. */
    explicit CatalogueSource(std::string ss_executable);

    CatalogueSource(const CatalogueSource&) = delete;
    CatalogueSource& operator=(const CatalogueSource&) = delete;

    /** @brief Spawns the read; a failed spawn finishes the source with an error. */
    void start();

    /** @brief Collects what the child has written and parses it once the output ends. */
    void poll();

    /** @brief Reports whether the catalogue has been read or the attempt has failed. */
    bool finished() const;

    /** @brief Returns the catalogue, empty before it is read and when the read failed. */
    const Catalogue& catalogue() const;

    /** @brief Returns why the catalogue could not be read, empty while it still can be. */
    const std::string& error() const;

private:
    /** @brief Parses what the child wrote into the catalogue or into the error. */
    void adopt_document();

    /** @brief Holds the `ss` program the read is spawned from. */
    std::string ss_executable_;

    /** @brief Holds the lines the read writes. */
    LineQueue queue_;

    /** @brief Holds the running read, null before start() and after a failed spawn. */
    std::unique_ptr<Process> process_;

    /** @brief Holds the document as the lines arrive, joined back together. */
    std::string document_;

    /** @brief Holds the catalogue once it has been read. */
    Catalogue catalogue_;

    /** @brief Holds the reason the read failed, empty while it still can succeed. */
    std::string error_;

    /** @brief Records that start() has been called. */
    bool started_ = false;

    /** @brief Records that there is nothing more to wait for. */
    bool finished_ = false;
};

}
}
