// IS3. Friends of a person
MATCH (n:Person { id: 37383395391076 })-[r:knows]-(friend)
RETURN
friend.id AS personId,
friend.firstName AS firstName,
friend.lastName AS lastName,
r.creationDate AS friendshipCreationDate
 ORDER BY
friendshipCreationDate DESC,
personId ASC;

// # 1  void folly::detail::function::call_<folly::futures::detail::Core<folly::Unit>::setCallback<folly::Future<folly::Unit>::thenErrorImpl<flavius::exec::BaseLookupJoinKeyStreamHandler::handleKeyBatchAndEnqueue(unsigned long, int, butil::IOBuf* const*, int, folly::Promise<folly::Unit>, std::shared_ptr<folly::exception_wrapper>)::$_5>(flavius::exec::BaseLookupJoinKeyStreamHandler::handleKeyBatchAndEnqueue(unsigned long, int, butil::IOBuf* const*, int, folly::Promise<folly::Unit>, std::shared_ptr<folly::exception_wrapper>)::$_5&&, folly::futures::detail::InlineContinuation) &&::{lambda(folly::Executor::KeepAlive<folly::Executor>&&, folly::Try<folly::Unit>&&)#1}>(flavius::exec::BaseLookupJoinKeyStreamHandler::handleKeyBatchAndEnqueue(unsigned long, int, butil::IOBuf* const*, int, folly::Promise<folly::Unit>, std::shared_ptr<folly::exception_wrapper>)::$_5&&, std::shared_ptr<folly::RequestContext>&&, folly::futures::detail::InlineContinuation)::{lambda(folly::futures::detail::CoreBase&, folly::Executor::KeepAlive<folly::Executor>&&, folly::exception_wrapper*)#1}, true, false, void, folly::futures::detail::CoreBase&, folly::Executor::KeepAlive<folly::Executor>&&, folly::exception_wrapper*>(folly::futures::detail::CoreBase&, folly::Executor::KeepAlive<folly::Executor>&&, folly::exception_wrapper*, folly::detail::function::Data&) at (unknown)
MATCH (n:Person { id: 37383395391076 })-[r:knows]-(friend)
RETURN
n.id,
friend.id AS personId,
friend.firstName AS firstName,
friend.lastName AS lastName,
r.creationDate AS friendshipCreationDate
LIMIT 10;

MATCH (n:Person { id: 37383395391076 })-[r:knows]-(friend)
RETURN
count(n), count(r), count(friend);

MATCH (n:Person )-[r:knows]->(friend)
RETURN
count(n), count(r), count(friend);

MATCH (n:Person )-[r:knows]->(friend)
RETURN r limit 10;


MATCH (n:Person { id: 37383395391076 })<-[r:knows]-(friend)
RETURN
count(n), count(r), count(friend);

MATCH (friend)<-[r:knows]-(n:Person { id: 37383395391076 })
RETURN
count(n), count(r), count(friend);

MATCH (n:Person { id: 37383395391076 })
RETURN n;

// MATCH (n:Person )-[r:knows]-(friend)
// RETURN
// n.id,
// friend.id AS personId,
// friend.firstName AS firstName,
// friend.lastName AS lastName,
// r.creationDate AS friendshipCreationDate
//  ORDER BY
// friendshipCreationDate DESC,
// personId ASC
// LIMIT 20;

// MATCH (n:Person )-[r:knows]-(friend)
// RETURN count(n), count(friend), count(r)
