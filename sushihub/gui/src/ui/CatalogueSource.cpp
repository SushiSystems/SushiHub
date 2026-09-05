/** @file CatalogueSource.cpp
 *  @brief Defines the spawn, the joining of the printed lines and the parse into a catalogue.
 *  @author Mustafa Garip
 */

#include "ui/CatalogueSource.hpp"

#include <utility>
#include <variant>

namespace SushiHub
{
namespace Gui
{

CatalogueSource::CatalogueSource(std::string ss_executable)
    : ss_executable_(std::move(ss_executable))
{
}

void CatalogueSource::start()
{
    if (started_)
    {
        return;
    }
    started_ = true;

    process_ = Process::start({ss_executable_, "--describe"}, queue_);
    if (process_ == nullptr)
    {
        error_ = "could not start " + ss_executable_;
        finished_ = true;
    }
}

void CatalogueSource::poll()
{
    if (finished_)
    {
        return;
    }

    std::string line;
    while (queue_.try_pop(line))
    {
        document_ += line;
        document_ += '\n';
    }

    if (queue_.closed() && queue_.empty())
    {
        adopt_document();
        finished_ = true;
    }
}

bool CatalogueSource::finished() const
{
    return finished_;
}

const Catalogue& CatalogueSource::catalogue() const
{
    return catalogue_;
}

const std::string& CatalogueSource::error() const
{
    return error_;
}

void CatalogueSource::adopt_document()
{
    if (document_.empty())
    {
        error_ = ss_executable_ + " printed no catalogue";
        return;
    }

    std::variant<Catalogue, ParseError> outcome = parse_catalogue(document_);
    if (const ParseError* failure = std::get_if<ParseError>(&outcome))
    {
        error_ = failure->reason;
        return;
    }
    catalogue_ = std::move(std::get<Catalogue>(outcome));
}

}
}
