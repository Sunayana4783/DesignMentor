"use client";
import { useState, Suspense, useEffect, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { quizApi } from "@/lib/api";
import type { QuizSession, QuizQuestion, QuizResult } from "@/types";
import ChatBubble from "@/components/ui/ChatBubble";
import MasteryBar from "@/components/ui/MasteryBar";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import { CheckCircle, XCircle, ArrowRight, Trophy } from "lucide-react";
import { clsx } from "clsx";

type Phase = "setup" | "quiz" | "result";

function QuizContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const defaultConcept = searchParams.get("concept") ?? "";

  const [conceptSlug, setConceptSlug] = useState(defaultConcept);
  const [phase, setPhase] = useState<Phase>("setup");
  const hasAutoStarted = useRef(false);

  // Auto-start quiz if concept provided in URL
  useEffect(() => {
    if (defaultConcept && !hasAutoStarted.current) {
      hasAutoStarted.current = true;
      setConceptSlug(defaultConcept);
      // delay to ensure auth token is loaded
      setTimeout(() => startQuizWithSlug(defaultConcept), 500);
    }
  }, [defaultConcept]);
  const [session, setSession] = useState<QuizSession | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<Record<string, { correct: boolean; evaluation: string }>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [inputVal, setInputVal] = useState("");

  const startQuizWithSlug = async (slug: string) => {
    if (!slug) return;
    setLoading(true);
    try {
      const { data } = await quizApi.start({ concept_slug: slug, num_questions: 5 });
      setSession(data);
      setCurrentIdx(0);
      setAnswers({});
      setFeedback({});
      setPhase("quiz");
    } catch (err: unknown) {
      console.error("Quiz start failed:", err);
      // Stay on setup page so user can retry manually
      setPhase("setup");
    } finally {
      setLoading(false);
    }
  };

  const startQuiz = async () => startQuizWithSlug(conceptSlug);

  const currentQ: QuizQuestion | undefined = session?.questions[currentIdx];

  const submitAnswer = async () => {
    if (!session || !currentQ || !inputVal.trim()) return;
    setLoading(true);
    const response = inputVal;
    setInputVal("");
    try {
      const { data } = await quizApi.answer({
        attempt_id: session.attempt_id,
        question_id: currentQ.id,
        user_response: response,
      });
      setAnswers((a) => ({ ...a, [currentQ.id]: response }));
      setFeedback((f) => ({
        ...f,
        [currentQ.id]: { correct: data.is_correct, evaluation: data.ai_evaluation },
      }));
    } catch (err) {
      // On error — mark as answered with a fallback so user can continue
      setAnswers((a) => ({ ...a, [currentQ.id]: response }));
      setFeedback((f) => ({
        ...f,
        [currentQ.id]: { correct: false, evaluation: "Could not evaluate — saved your answer. Continue to next question." },
      }));
    } finally {
      setLoading(false);
    }
  };

  const nextQuestion = () => {
    if (currentIdx + 1 < (session?.questions.length ?? 0)) {
      setCurrentIdx((i) => i + 1);
    }
  };

  const finishQuiz = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const { data } = await quizApi.complete(session.attempt_id);
      setResult(data);
      setPhase("result");
    } finally {
      setLoading(false);
    }
  };

  const answeredCurrent = currentQ ? !!answers[currentQ.id] : false;
  const allAnswered = session ? session.questions.every((q) => !!answers[q.id]) : false;
  const isLastQuestion = session ? currentIdx === session.questions.length - 1 : false;

  if (phase === "setup") return (
    <div className="p-6 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-2">Quiz Mode</h1>
      <p className="text-slate-400 text-sm mb-8">Test your understanding with AI-generated questions</p>
      <div className="bg-surface-card border border-surface-border rounded-xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Concept slug</label>
          <input
            value={conceptSlug}
            onChange={(e) => setConceptSlug(e.target.value)}
            placeholder="e.g. dependency-inversion"
            className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
        <button
          onClick={startQuiz} disabled={!conceptSlug || loading}
          className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition-colors text-sm"
        >
          {loading ? <Spinner size={4} /> : "Start Quiz →"}
        </button>
      </div>
    </div>
  );

  if (phase === "result" && result) return (
    <div className="p-6 max-w-2xl mx-auto animate-fade-in">
      <div className="bg-surface-card border border-surface-border rounded-xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <Trophy className={clsx("w-8 h-8", result.passed ? "text-yellow-400" : "text-slate-500")} />
          <div>
            <h2 className="text-xl font-bold text-white">{result.passed ? "Concept Passed! 🎉" : "Keep Practising"}</h2>
            <p className="text-slate-400 text-sm capitalize">{result.concept_slug.replace(/-/g, " ")}</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { label: "Score",    value: `${result.percentage.toFixed(0)}%` },
            { label: "Points",   value: `${result.score.toFixed(0)}/${result.max_score.toFixed(0)}` },
            { label: "Mastery",  value: result.mastery_level },
          ].map(({ label, value }) => (
            <div key={label} className="bg-surface rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-white">{value}</p>
              <p className="text-xs text-slate-500 mt-1">{label}</p>
            </div>
          ))}
        </div>

        <MasteryBar score={result.percentage} level={result.mastery_level} height="h-2.5" />

        <p className="text-slate-300 text-sm mt-4">{result.ai_feedback}</p>

        {result.weak_subtopics.length > 0 && (
          <div className="mt-4">
            <p className="text-xs text-slate-500 mb-2">Weak areas to review:</p>
            <div className="flex flex-wrap gap-2">
              {result.weak_subtopics.map((t) => <Badge key={t} variant="warning">{t}</Badge>)}
            </div>
          </div>
        )}

        <div className="flex gap-3 mt-6">
          {result.next_action === "next_concept" && result.next_concept_slug && (
            <button
              onClick={() => router.push(`/learn?concept=${result.next_concept_slug}`)}
              className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
            >
              Next Concept <ArrowRight className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => { setPhase("setup"); setResult(null); }}
            className="text-sm text-slate-400 hover:text-white px-4 py-2 border border-surface-border rounded-lg transition-colors"
          >
            Try another concept
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto px-6 py-4">
      {/* Progress */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-slate-400 mb-1.5">
          <span>Question {currentIdx + 1} of {session?.questions.length}</span>
          <span>{Object.keys(answers).length} answered</span>
        </div>
        <div className="w-full bg-surface-border rounded-full h-1.5">
          <div
            className="bg-brand-500 h-1.5 rounded-full transition-all"
            style={{ width: `${((currentIdx + 1) / (session?.questions.length ?? 1)) * 100}%` }}
          />
        </div>
      </div>

      {/* Question */}
      {currentQ && (
        <div className="bg-surface-card border border-surface-border rounded-xl p-5 mb-4 flex-shrink-0">
          <div className="flex items-center gap-2 mb-3">
            <Badge variant={currentQ.difficulty === "hard" ? "danger" : currentQ.difficulty === "medium" ? "warning" : "success"}>
              {currentQ.difficulty}
            </Badge>
            <Badge>{currentQ.question_type.replace("_", " ")}</Badge>
            <span className="text-xs text-slate-500 ml-auto">{currentQ.points} pts</span>
          </div>
          <p className="text-white font-medium text-sm leading-relaxed">{currentQ.content}</p>

          {/* MCQ options */}
          {currentQ.options && currentQ.options.length > 0 && !answeredCurrent && (
            <div className="mt-4 space-y-2">
              {currentQ.options.map((opt) => (
                <button
                  key={opt}
                  onClick={() => setInputVal(opt.charAt(0))}
                  className={clsx(
                    "w-full text-left text-sm px-3 py-2.5 rounded-lg border transition-colors",
                    inputVal.startsWith(opt.charAt(0))
                      ? "border-brand-500 bg-brand-600/20 text-brand-300"
                      : "border-surface-border text-slate-300 hover:border-slate-400"
                  )}
                >
                  {opt}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Feedback */}
      {currentQ && answers[currentQ.id] && feedback[currentQ.id] && (
        <div className={clsx(
          "rounded-xl p-4 mb-4 flex-shrink-0 border text-sm",
          feedback[currentQ.id].correct
            ? "bg-green-900/20 border-green-800 text-green-300"
            : "bg-red-900/20 border-red-800 text-red-300"
        )}>
          <div className="flex items-center gap-2 mb-2 font-medium">
            {feedback[currentQ.id].correct
              ? <><CheckCircle className="w-4 h-4" /> Correct!</>
              : <><XCircle className="w-4 h-4" /> Not quite</>
            }
          </div>
          <p className="text-slate-300">{feedback[currentQ.id].evaluation}</p>
        </div>
      )}

      {/* Input + controls */}
      <div className="mt-auto space-y-3">
        {!answeredCurrent && (
          <div className="flex gap-3">
            {(!currentQ?.options || currentQ.options.length === 0) && (
              <textarea
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                placeholder="Type your answer…"
                rows={2}
                className="flex-1 bg-surface border border-surface-border rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
              />
            )}
            <button
              onClick={submitAnswer} disabled={!inputVal.trim() || loading}
              className="bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white text-sm font-semibold px-5 py-2 rounded-xl transition-colors self-end"
            >
              {loading ? <Spinner size={4} /> : "Submit"}
            </button>
          </div>
        )}

        {answeredCurrent && (
          <div className="flex gap-3 justify-end">
            {!isLastQuestion ? (
              <button onClick={nextQuestion} className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
                Next <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button onClick={finishQuiz} disabled={loading} className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
                {loading ? <Spinner size={4} /> : <><Trophy className="w-4 h-4" /> Finish Quiz</>}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function QuizPage() {
  return <Suspense><QuizContent /></Suspense>;
}
